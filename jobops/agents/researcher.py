"""Company researcher — deep-dive on qualified jobs before drafting.

Runs only after the scorer gate passes (prerequisite-gate pattern).
Output feeds the tailoring agents so cover letters cite real, current
facts about the company instead of generic flattery.
"""

from ..client import ask_with_search


def research_company(job: dict) -> str:
    return ask_with_search(
        f"""Research {job["company"]} to prepare a job application for the role
"{job["title"]}" ({job.get("url", "no url")}).

Produce a concise briefing with these sections:
1. WHAT THEY DO — products/services, customers, business model
2. AI POSTURE — how they use or sell AI today; any Claude/Anthropic,
   OpenAI, or agent-platform partnerships or public AI initiatives
3. RECENT NEWS — last 6 months: funding, launches, leadership, Austin
   presence/office news if any
4. TEAM & CULTURE SIGNALS — what they seem to value in hires
5. TALKING POINTS — 3 specific hooks a candidate could use in a cover
   letter or interview, each tied to a fact found above

Only include facts you actually found; mark anything uncertain as such.""",
        system="You are a company research analyst preparing a candidate for a job application.",
        max_searches=8,
    )
