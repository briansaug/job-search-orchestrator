# Architecture Notes

Design rationale, pattern by pattern. Written to double as a case study in
Claude orchestration design (the same patterns tested in the Claude Certified
Architect curriculum).

## 1. Hub-and-spoke orchestration

The CLI (`jobops/cli.py`) is the hub. Specialist agents — scouts, scorer,
researcher, tailors — are spokes that never talk to each other directly.
All context passes through the hub via the tracker's job records.

*Why not a swarm?* Deterministic control flow. The pipeline order
(score before research before draft) encodes a business rule: don't spend
money researching a job we'd reject. Code-controlled orchestration makes
that rule enforceable; agent-to-agent chatter would make it a suggestion.

## 2. Prerequisite gate (cheap triage before expensive work)

`scorer.gate()` maps a 0-10 fit score to a stage:

| score | stage | what happens |
|---|---|---|
| ≥ 7 | qualified | auto: research + draft package |
| 5-6 | borderline | held for human decision |
| < 5 | rejected | recorded, nothing spent |

Cost shape: a score is one small structured call; a research+draft package
is ~10 web searches plus four long generations. The gate means the expensive
path only runs on jobs worth applying to.

## 3. Structured outputs at every data boundary

Two flavors, used deliberately:

- **Free text inside an agent's own reasoning** — the scout's search
  narrative, the researcher's briefing. Prose is fine here; a human or a
  downstream prompt consumes it whole.
- **JSON schema whenever data enters the tracker** — job records
  (`EXTRACT_SCHEMA`) and score verdicts (`SCORE_SCHEMA`) use
  `output_config.format` so the pipeline never parses prose into fields.
  The score field is an integer enum 0-10: the model cannot return "7.5/10,
  maybe 8" — the schema forbids it.

## 4. Server-side tools (web_search)

Discovery and research use Anthropic's `web_search_20260209` server tool —
no scraping infrastructure, no result parsing; the model issues queries and
reads results server-side. The client handles the `pause_turn` stop reason
(the server tool loop yields control every 10 iterations and expects a
re-send to continue) with a bounded continuation loop.

`max_uses` caps searches per call — the cost-control knob on every
search-bearing agent.

## 5. Human-in-the-loop trust boundary

The system's write-authority ends at the local filesystem. Submitting an
application, sending an outreach message — anything outward-facing — is a
human action recorded after the fact via `jobops mark`. The stage model
makes the boundary auditable: every transition is timestamped in the job's
history.

## 6. State, checkpointing, resumption

`data/jobs.json` is the single state store. `cmd_process` saves after every
expensive step (score, research, draft), so a crash or Ctrl-C never loses
paid-for work — re-running picks up exactly where it stopped. Job identity
is a slug of company+title, which doubles as the dedupe key so scouts can
re-find the same posting harmlessly.

## 7. Cost design

- Default model `claude-sonnet-5` (cost-balanced: near-Opus agentic quality
  at $3/$15 per MTok, intro $2/$10 through 2026-08-31); any run can override
  with `JOBOPS_MODEL=claude-opus-4-8` ($5/$25) when quality matters more, or
  pick per-run from the cockpit's model dropdown. Sonnet 5 runs adaptive
  thinking by default, which bills into `max_tokens` — output budgets carry
  headroom for it.
- Batched processing (`max_jobs_per_process_run`) keeps a single run's
  spend predictable.
- The gate (see §2) is the biggest lever: most discovered jobs never reach
  the expensive path.

## 8. Interactive elicitation is a skill, not a subagent

The intake interviewer (`/jobops-intake`) needs mid-task dialogue with the
user. Subagents run headless — they spawn, work, and return once — so a
questionnaire inside one would either stall or answer its own questions.
The rule encoded here: if the human participates mid-task, the work belongs
to the main loop (a skill); if the human only reviews the output, it can be
a spoke. Intake also reuses the §6 pattern at conversation scale:
`profile/intake_state.json` checkpoints phase progress (P0–P6), so a
dropped sitting resumes exactly where it stopped.

## 9. Verification tags — a trust boundary as data

`profile/facts.yaml` turns the "no invented metrics" policy from prose into
data: every claim carries `documented | estimated | guess`. Downstream
agents don't interpret policy, they filter on a field — documented facts
may be quoted verbatim, estimates only as rounded ranges, guesses never.
Same move as the score gate (§2): a business rule becomes enforceable the
moment it's structured data instead of instructions. This ledger is what
the claims-auditor (roadmap session C) will diff every draft against.

## Known limitations / next steps

- LinkedIn can't be scouted automatically (anti-bot) — the `add` command is
  the manual intake path.
- The people lane (referrals, outreach, follow-ups) and interview lane are
  designed but not yet built — build order in `docs/capability-roadmap.md`.
- Outcome analytics (application → interview conversion by source/score)
  once real data accumulates — ships as the metrics-analyst (roadmap
  session D).
