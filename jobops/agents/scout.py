"""Scout agents — discovery via the web_search server tool.

Two-stage pattern: a search pass returns free text with findings, then a
structured-extraction pass converts it into clean job records. Keeping the
stages separate means the search agent can think freely and the extractor
guarantees schema-valid data for the tracker.
"""

from ..client import ask_structured, ask_with_search
from ..config import load_search_profile, load_target_companies

EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "jobs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "location": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["company", "title", "url", "location", "summary"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["jobs"],
    "additionalProperties": False,
}


def _search_prompt(companies: list[str], profile: dict) -> str:
    roles = ", ".join(profile["target_roles"])
    return f"""Search for currently-open job postings matching this profile:

TARGET ROLES: {roles}
LOCATION: Austin, TX metro (in-person/hybrid preferred) OR fully remote US roles
KEYWORDS THAT SIGNAL FIT: {", ".join(profile["keywords"])}

Search the career pages and job listings of these companies: {", ".join(companies)}

Also run 1-2 general searches like "AI solutions architect jobs Austin TX"
to catch postings outside that list.

For every real, currently-open posting you find, report: company, exact job
title, direct URL to the posting, location/remote status, and a 2-3 sentence
summary of the role and requirements. Only include postings you actually
found via search — do not invent or guess listings. If a company has nothing
relevant open, skip it silently."""


def run_scouts(max_searches_per_group: int = 8) -> list[dict]:
    """Run one scout per company group; return extracted job dicts."""
    profile = load_search_profile()
    groups = load_target_companies()
    found: list[dict] = []

    for group_name, companies in groups.items():
        print(f"  scout [{group_name}]: searching...")
        report = ask_with_search(
            _search_prompt(companies, profile),
            system="You are a job-market scout. Be factual; never fabricate listings.",
            max_searches=max_searches_per_group,
        )
        extracted = ask_structured(
            "Extract every job posting from this scout report into the schema. "
            "Skip anything that is not a specific, real job posting with a URL.\n\n"
            + report,
            schema=EXTRACT_SCHEMA,
        )
        jobs = extracted["jobs"]
        print(f"  scout [{group_name}]: {len(jobs)} posting(s) extracted")
        for j in jobs:
            j["source"] = f"scout:{group_name}"
        found.extend(jobs)

    return found
