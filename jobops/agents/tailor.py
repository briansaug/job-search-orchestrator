"""Tailoring agents — produce the draft application package.

Three artifacts per job, written to data/drafts/<job-id>/:
  resume_bullets.md  — profile experience rewritten for THIS posting
  cover_letter.md    — grounded in the researcher's briefing
  outreach.md        — short LinkedIn/email note to a hiring manager

Nothing here is ever submitted automatically. The drafts land in the
review queue; Brian is the only one who hits send.
"""

from ..client import ask
from ..tracker import drafts_dir_for

_STYLE = """Write like a sharp, direct human — no AI-sounding filler
("I am excited to", "I believe my skills align"), no buzzword chains,
no flattery without a fact behind it. Short sentences. Specific claims."""


def draft_package(job: dict, master_profile: str, research: str) -> list[str]:
    context = f"""CANDIDATE MASTER PROFILE:
{master_profile}

JOB:
{job["company"]} — {job["title"]} ({job.get("location", "")})
{job.get("description") or job.get("summary", "")}

COMPANY RESEARCH BRIEFING:
{research}

SCORING ANGLE (lead with this): {(job.get("score_detail") or {}).get("angle", "n/a")}
"""

    bullets = ask(
        context + "\nTASK: Write 6-8 resume bullet points selected and reworded "
        "from the master profile to best match this posting. Each bullet: strong "
        "verb, specific claim, quantified where the profile allows. Flag any "
        "bullet that needs a number Brian must supply as [NEEDS METRIC].",
        system=_STYLE, max_tokens=4096,
    )
    letter = ask(
        context + "\nTASK: Write a cover letter, max 250 words. Structure: "
        "(1) a specific hook from the company research, (2) the candidate's "
        "angle for this role with one proof point, (3) a second proof point, "
        "(4) direct close. No generic praise.",
        system=_STYLE, max_tokens=4096,
    )
    outreach = ask(
        context + "\nTASK: Write a 60-90 word LinkedIn message to the likely "
        "hiring manager for this role. Reference one company-specific fact, "
        "state the candidate's angle in one sentence, ask for a short call.",
        system=_STYLE, max_tokens=2048,
    )

    d = drafts_dir_for(job)
    (d / "resume_bullets.md").write_text(bullets)
    (d / "cover_letter.md").write_text(letter)
    (d / "outreach.md").write_text(outreach)
    return [str(d / n) for n in ("resume_bullets.md", "cover_letter.md", "outreach.md")]
