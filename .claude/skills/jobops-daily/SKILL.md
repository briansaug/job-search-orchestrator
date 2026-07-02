---
name: jobops-daily
description: Daily job-search pipeline run through the Claude Code harness — scout fresh AI-architect postings, score them against Brian's profile, research and draft applications for qualified ones, and write a morning briefing. Use when asked to run the daily job pipeline, scout jobs, or process pending jobs. Supports args "scout-only" and "process-only".
---

# JobOps daily pipeline (Claude Code surface)

You are the orchestrator, scorer, researcher, and writer in one harness run.
This skill mirrors the Python pipeline in `jobops/` but runs entirely through
Claude Code (subscription-powered, no API key). Both surfaces share the same
state files, so never diverge from the schemas below.

Modes: no args = full daily run. `scout-only` = steps 1–3 + briefing.
`process-only` = steps 4–6 + briefing (skip discovery).

## Context to load first

- `config/search_profile.yaml` — target roles, keywords, location prefs, gates
- `config/target_companies.yaml` — company watchlist by group
- `profile/master_profile.md` — the candidate (Brian Bruner)
- `data/jobs.json` — pipeline state (create as `[]` if missing)

## Step 1 — Scout (WebSearch)

Search for job postings that match the search profile, prioritizing postings
from the LAST 7 DAYS (this runs daily — freshness beats volume):

- 2–3 searches per company group from the watchlist (e.g. "KUNGFU.AI careers
  AI solutions", "Accenture AI solutions architect Austin")
- 2–3 general searches: "AI solutions architect jobs Austin TX", "AI
  implementation consultant remote", plus one keyword rotation of your choice
- Cap total searches around 12 per run

Only record real postings you actually found, with URLs. Never fabricate.

## Step 2 — Dedupe

A job's `id` is the slug of company+title: lowercase, non-alphanumerics → `-`,
trimmed to 60 chars (e.g. "KUNGFU.AI" + "AI Solutions Consultant" →
`kungfu-ai-ai-solutions-consultant`). Skip any id already in `data/jobs.json`.

## Step 3 — Record new jobs

Append each new job to `data/jobs.json` with exactly this shape:

```json
{
  "id": "<slug>",
  "company": "...", "title": "...", "url": "...",
  "description": "<2-3 sentence summary of role + requirements>",
  "source": "scout:claude-code",
  "stage": "scouted",
  "found_on": "<today ISO date>",
  "score": null, "score_detail": null, "research": null,
  "history": ["<today>: scouted via scout:claude-code"]
}
```

## Step 4 — Score & gate (max 3 jobs per run)

For each job in stage `scouted` (oldest first, at most 3 per run), score 0–10:

- Role match: genuinely an AI solutions/consulting/enablement role, ideally
  Claude/Anthropic-adjacent? Career-changer fit — Brian is senior in
  business/strategy with certified hands-on Claude skills, NOT a career
  software engineer; heavy pure-engineering requirements are a red flag.
- Location: Austin metro in-person/hybrid highest; strong remote acceptable;
  other-city in-person ≈ 0.
- Comp signal vs. the floor in the search profile.

Be honest — an inflated score wastes Brian's time. Set:

```json
"score": <int 0-10>,
"score_detail": {"score": <int>, "location_fit": "austin_local|remote|other",
  "rationale": "...", "red_flags": ["..."],
  "angle": "<the one thing THIS employer would care most about>"}
```

Gate (from `pipeline` in search_profile.yaml): score ≥ 7 → stage `qualified`;
5–6 → `borderline`; < 5 → `rejected`. Append a history line
`"<today>: → <stage> (score N/10)"`. Save `data/jobs.json` after each job.

## Step 5 — Research qualified jobs (WebSearch)

For each job that just became `qualified`: research the company — what they
do, AI posture (Claude/Anthropic/agent partnerships), last-6-months news,
Austin presence, hiring signals, and 3 fact-backed talking points. Store the
briefing in the job's `"research"` field, set stage `researched`, save.

## Step 6 — Draft the application package

For each `researched` job, write to `data/drafts/<id>/`:

- `resume_bullets.md` — 6–8 bullets reworded from the master profile for this
  posting; mark missing numbers `[NEEDS METRIC]`
- `cover_letter.md` — ≤250 words: research-based hook → angle + proof point →
  second proof point → direct close
- `outreach.md` — 60–90 word LinkedIn note to the likely hiring manager

Style: sharp, direct, human. No AI-filler ("I am excited to..."), no unfounded
flattery, short sentences, specific claims. Set stage `drafted`, save.

## Step 7 — Briefing & dashboard

Rewrite `data/STATUS.md` (jobs grouped by stage, with scores). Write
`data/BRIEFING.md`: today's date, new postings found, scores given, drafts
awaiting Brian's review (with file paths), and anything in `borderline`
needing his decision. Keep it scannable — it's his morning read.

## Hard rules

- NEVER submit, send, or post anything anywhere. Drafts only. Brian is the
  only actor who submits applications.
- Never edit `profile/master_profile.md` or anything under `config/`.
- Never invent job postings, company facts, or metrics.
- End with a 3-5 line summary: found / scored / drafted / needs-Brian.
