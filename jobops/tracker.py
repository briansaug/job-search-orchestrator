"""Pipeline state store — every job moves through explicit stages.

Stages:
  scouted    → found by a scout agent or added manually
  qualified  → passed the fit-score gate (score >= gate)
  borderline → mid score; held for Brian's manual call
  rejected   → below the gate; kept for the record
  researched → company deep-dive attached
  drafted    → application materials written to data/drafts/<slug>/
  submitted  → Brian reviewed and submitted (manual `mark`)
  response / interview / offer / closed — outcome tracking (manual `mark`)
"""

import json
import re
from datetime import date

from .config import DATA_DIR, DRAFTS_DIR, JOBS_FILE

STAGES = ["scouted", "qualified", "borderline", "rejected", "researched",
          "drafted", "submitted", "response", "interview", "offer", "closed"]


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def load_jobs() -> list[dict]:
    if JOBS_FILE.exists():
        return json.loads(JOBS_FILE.read_text())
    return []


def save_jobs(jobs: list[dict]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    JOBS_FILE.write_text(json.dumps(jobs, indent=2))


def add_job(jobs: list[dict], company: str, title: str, url: str = "",
            description: str = "", source: str = "manual") -> dict | None:
    """Add a job unless we already track it (dedupe on company+title)."""
    slug = _slugify(f"{company}-{title}")
    if any(j["id"] == slug for j in jobs):
        return None
    job = {
        "id": slug,
        "company": company,
        "title": title,
        "url": url,
        "description": description,
        "source": source,
        "stage": "scouted",
        "found_on": date.today().isoformat(),
        "score": None,
        "score_detail": None,
        "research": None,
        "history": [f"{date.today().isoformat()}: scouted via {source}"],
    }
    jobs.append(job)
    return job


def set_stage(job: dict, stage: str, note: str = "") -> None:
    assert stage in STAGES, f"unknown stage: {stage}"
    job["stage"] = stage
    entry = f"{date.today().isoformat()}: → {stage}"
    if note:
        entry += f" ({note})"
    job["history"].append(entry)


def drafts_dir_for(job: dict):
    d = DRAFTS_DIR / job["id"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def dashboard(jobs: list[dict]) -> str:
    """Human-readable pipeline summary, also written to data/STATUS.md."""
    lines = ["# Job Pipeline Status", ""]
    for stage in STAGES:
        stage_jobs = [j for j in jobs if j["stage"] == stage]
        if not stage_jobs:
            continue
        lines.append(f"## {stage.upper()} ({len(stage_jobs)})")
        for j in stage_jobs:
            score = f" — score {j['score']}/10" if j["score"] is not None else ""
            lines.append(f"- **{j['company']}** · {j['title']}{score}")
            if j.get("url"):
                lines.append(f"  <{j['url']}>")
        lines.append("")
    text = "\n".join(lines)
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "STATUS.md").write_text(text)
    return text
