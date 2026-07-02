# CLAUDE.md

Project context for Claude Code — read this first.

## What this is

JobOps: Brian Bruner's multi-agent job-search orchestrator, targeting an
AI Solutions Architect / AI Enablement role (Austin metro in-person/hybrid
preferred; remote OK if strong fit + comp). Doubles as a public portfolio
piece: <https://github.com/briansaug/job-search-orchestrator>.

## How to work with Brian

Brian is not a coder — you write and run everything; explain the why/what.
He is studying for the Claude Certified Architect (Foundations) exam
(workspace: `~/claude-certification-guide`), so tie design decisions to
exam concepts (orchestration, gates, tool design, structured outputs) when
teaching.

## Two run surfaces, one state

1. **Claude API** (`jobops/` Python, `.venv` on Python 3.12 — system 3.9 is
   too old): `.venv/bin/python -m jobops scout|add|process|status|mark|selftest`.
   Billed per token via `.env` key. This is the portfolio reference — keep
   it Claude-native (server-side web_search + structured outputs).
2. **Claude Code harness** (`.claude/skills/jobops-daily/`): `/jobops-daily`
   or headless `claude -p "/jobops-daily"` — subscription-billed. A launchd
   job (`com.brianbruner.jobops-daily`, see docs/scheduling.md) runs it
   daily at 8:00 AM, logging to `data/cron.log`, ending in `data/BRIEFING.md`.

Both surfaces share `data/jobs.json` (schema documented in the skill) and
the gates in `config/search_profile.yaml` (≥7 qualified / 5–6 borderline /
<5 rejected).

## Hard rules

- **Nothing is ever submitted, sent, or posted by an agent.** Drafts only;
  Brian is the sole submitter. `jobops mark <id> submitted` records his act.
- **Metrics policy** (in `profile/master_profile.md`): approved numbers only
  (SAUG 100+ audience; Bruner Media 12+ end-to-end engagements). Never
  invent or extrapolate; weak scale → reframe on depth/artifacts.
- `profile/master_profile.md`, `data/`, `.env` are gitignored — never
  commit personal data; repo is public.
- Subagent `resume-researcher` (`.claude/agents/`) is read-only by design.

## Status (2026-07-01)

- First live run: 8 postings tracked. **Nimble Gravity — AI Enablement &
  Adoption Manager (9/10, drafted, near submission-ready)**; borderlines
  Accenture-Austin + Glean await Brian's pursue/pass; 4 Anthropic roles
  queued (expect low scores: SF/NYC + engineering bar).
- Resume research report: `data/research/resume-research-2026-07-01.md`
  (fork enablement vs. architect resume variants; skills block added).
- Blocking on Brian: SAUG adoption metric, Bruner Media years + prior
  career, LinkedIn URL, remaining `[FILL IN]`s in master profile.

## Roadmap (agreed 2026-07-01 — each is its own future session)

1. **Resume & profile session** — gather everything the orchestration needs:
   full work history, metrics, STAR stories; finalize master_profile.md.
2. **Portfolio website session** — build from the two local drafts
   (`~/Brian-Bruner-Portfolio-Website{,-2}`); include the "Let Us Entertain
   You" NotebookLM training notebook (built for Aba), referrals &
   testimonials, committee memberships.
3. **Success-metrics session** — define success parameters (interviews =
   output; applications/day, outreach sent, response rate = inputs), build
   a tracking spreadsheet, and design the roster of additional subagents
   and skills needed to hit those numbers.
