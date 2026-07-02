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
2. **Claude Code harness** (`.claude/skills/`): `/jobops-daily` (pipeline;
   headless `claude -p "/jobops-daily"`) and `/jobops-intake` (guided
   onboarding interview, P0–P6) — subscription-billed. A launchd
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
- **Verification tags** (`profile/facts.yaml`): `documented` numbers may be
  quoted verbatim; `estimated` only as rounded ranges; `guess` never
  appears in any agent output.
- `profile/master_profile.md`, `profile/facts.yaml`, `profile/contacts.json`,
  `profile/intake_state.json`, `data/`, `.env` are gitignored — never
  commit personal data; repo is public. Contacts are other people's PII
  and never leave the machine.
- Subagent `resume-researcher` (`.claude/agents/`) is read-only by design.

## Status (2026-07-02)

- 2026-07-02: Capability roadmap researched via 3 parallel subagents →
  `docs/capability-roadmap.md` (raw reports in `data/research/`). Session A
  shipped: `/jobops-intake` skill (P0–P6, resumable), profile schema v2
  template, `facts.yaml` + `contacts.json` ledgers, gitignore coverage.
  Brian has NOT yet run the questionnaire — profile still has `[FILL IN]`s.
- First live run: 8 postings tracked. **Nimble Gravity — AI Enablement &
  Adoption Manager (9/10, drafted, near submission-ready)**; borderlines
  Accenture-Austin + Glean await Brian's pursue/pass; 4 Anthropic roles
  queued (expect low scores: SF/NYC + engineering bar).
- Resume research report: `data/research/resume-research-2026-07-01.md`
  (fork enablement vs. architect resume variants; skills block added).
- Blocking on Brian: SAUG adoption metric, Bruner Media years + prior
  career, LinkedIn URL, remaining `[FILL IN]`s in master profile.

## Roadmap (superseded 2026-07-02 — canonical: docs/capability-roadmap.md)

Build order A–F, researched via three parallel subagents:

- **A — intake (DONE 2026-07-02):** `/jobops-intake` P0–P6 questionnaire,
  profile v2, `facts.yaml`, `contacts.json`.
- **B — referral lane (next):** referral-pathfinder + outreach-drafter
  subagents + `/outreach`; wire into `/jobops-daily` for every job ≥7.
- **C — trust & follow-through:** claims-auditor draft gate,
  followup-manager, `/follow-ups`, jobs.json field extensions.
- **D — measurement:** metrics-analyst, `/pipeline-review`, `/debrief`.
- **E — interview lane:** prep-coach + mock-interviewer + skills.
- **F — visibility:** profile-optimizer, portfolio-builder (absorbs the old
  portfolio-website session: `~/Brian-Bruner-Portfolio-Website{,-2}`, the
  "Let Us Entertain You" NotebookLM notebook for Aba, referrals &
  testimonials, committees), ghost-job-screener.

The old "resume & profile session" = running intake P1–P2 with Brian — the
tooling now exists; the conversation still needs to happen.
