"""Fit scorer — the prerequisite gate of the pipeline.

Returns a structured verdict; downstream agents (researcher, tailor) only
run when the score clears the gate in config/search_profile.yaml. This is
the human-in-the-loop trust boundary in miniature: cheap triage before
expensive work.
"""

import yaml

from ..client import ask_structured
from ..config import load_search_profile

SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "enum": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
        "location_fit": {"type": "string", "enum": ["austin_local", "remote", "other"]},
        "rationale": {"type": "string"},
        "red_flags": {"type": "array", "items": {"type": "string"}},
        "angle": {"type": "string"},
    },
    "required": ["score", "location_fit", "rationale", "red_flags", "angle"],
    "additionalProperties": False,
}


def score_job(job: dict, master_profile: str) -> dict:
    profile = load_search_profile()
    result = ask_structured(
        f"""Score this job posting 0-10 for fit against the candidate.

SCORING RUBRIC:
- Role match to target roles and keywords (is this genuinely an AI
  solutions/consulting/enablement role, ideally Claude/Anthropic-adjacent?)
- Location: Austin metro in-person/hybrid scores highest; strong remote
  roles are acceptable; other-city in-person roles score near zero.
- Requirements realism: the candidate is a career-changer — senior in
  business/strategy, certified-and-hands-on with Claude, NOT a career
  software engineer. Heavy pure-engineering requirements are a red flag.
- Compensation signal vs. floor of ${profile["compensation"]["minimum_base_usd"]:,}.

Also give: the single strongest "angle" — the one thing about this candidate
this specific employer would care most about.

SEARCH PREFERENCES:
{yaml.safe_dump(profile)}

CANDIDATE MASTER PROFILE:
{master_profile}

JOB POSTING:
Company: {job["company"]}
Title: {job["title"]}
Location: {job.get("location", "unknown")}
URL: {job.get("url", "")}
Description/summary:
{job.get("description") or job.get("summary", "(none — judge from title/company)")}""",
        schema=SCORE_SCHEMA,
        system="You are a rigorous job-fit assessor. Be honest — an inflated score wastes the candidate's time.",
    )
    return result


def gate(score: int) -> str:
    """Map a score to the next pipeline stage."""
    profile = load_search_profile()
    if score >= profile["pipeline"]["score_gate_qualified"]:
        return "qualified"
    if score >= profile["pipeline"]["score_gate_borderline"]:
        return "borderline"
    return "rejected"
