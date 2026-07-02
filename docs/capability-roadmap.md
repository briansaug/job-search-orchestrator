# JobOps capability roadmap

*Written 2026-07-02. Synthesized from three parallel research sub-agents
(job-search funnel science · agentic tooling patterns · intake questionnaire
design). Raw source-cited reports live locally in `data/research/`
(gitignored). This document is the build plan for turning JobOps from an
application pipeline into a full job-search operating system anyone can adopt.*

## What the evidence says (design principles)

1. **Relationships outrank volume.** Referrals supply 30–50% of hires and
   convert at ~28–34% vs ~2.7–5% for cold applications — one referral ≈ 40
   cold applies. The current pipeline optimizes the *application* lane; the
   biggest missing lane is *people*: warm paths, outreach, informational
   interviews.
2. **Trust is the moat.** ~80% of hiring managers say they discard obviously
   AI-generated applications, and resume "conflation" (mixing facts across
   jobs) happens at every model tier. Every claim an agent writes must trace
   to a verified fact the user tagged as documented. A blocking audit gate,
   not a style preference.
3. **The human sends everything.** Auto-apply tools get accounts banned
   (LinkedIn blacklists 461 plugins) and convert at 0.1–2%. JobOps's
   draft-only rule is not a limitation — it's the reason the system works.
   Permanent invariant.
4. **Instrument the funnel; let outcomes tune the system.** Low response rate
   → targeting/keywords problem. Responses but no interviews → positioning
   problem. Interviews but no offers → prep problem. One experiment at a
   time, 2-week stop rule, weekly review.
5. **Freshness beats breadth in discovery.** ~20–30% of postings are "ghost
   jobs"; popular postings draw 150+ applications in days. Applying within
   24–72h of posting matters more than adding more job boards.

## Target architecture — three build layers

| Layer | What it is | Where it lives |
|---|---|---|
| **Sub-agents** | Specialist workers with narrow missions and scoped tools | `.claude/agents/*.md` |
| **Skills** | Reusable slash-command workflows the user (or cron) invokes | `.claude/skills/*/SKILL.md` |
| **Tools & data stores** | MCP connections, scripts, and the shared state files that pass context between agents | `config/`, `data/`, MCP |

## Sub-agent roster

Existing: scout, scorer (gate), company-researcher, tailor (all inside
`/jobops-daily`), plus the read-only `resume-researcher` sub-agent.

### Tier 1 — build now

| Sub-agent | Mission | Needs | Human checkpoint |
|---|---|---|---|
| **intake-interviewer** | Run the P0–P6 onboarding questionnaire (below); build profile v2, facts ledger, network map | conversation, profile files | user answers; approves read-back |
| **referral-pathfinder** | For every job scored ≥7, map 3–5 named warm/adjacent paths in (2nd-degree, alumni, communities) with evidence | WebSearch, contacts store, researcher output | user picks whom to approach |
| **outreach-drafter** | Personalized LinkedIn notes (<400 chars) & emails to identified contacts; informational-interview asks | facts ledger, pathfinder output, Gmail-draft MCP (optional) | user edits & sends every message |
| **claims-auditor** | Blocking QA gate on every tailor draft: verify each bullet against `facts.yaml`, flag hallucination/conflation/AI-generic phrasing | file read, structured output | runs *before* the user ever sees a draft |
| **followup-manager** | Sweep state for stale threads; draft thank-yous (<24h) and rule-of-three follow-ups (3–5d, 7–10d); mark >45d as silent rejection | state store, Calendar/Gmail MCP (optional) | user sends |
| **metrics-analyst** | Weekly funnel report: stage conversions by channel & resume variant; diagnosis + reallocation recommendation | state store, metrics snapshots | user approves pivots |

### Tier 2 — build next

| Sub-agent | Mission | Needs | Human checkpoint |
|---|---|---|---|
| **interview-prep-coach** | Per-interview prep pack: likely questions from JD, company talking points, STAR stories mapped from ledger | WebSearch, state store | user studies pack |
| **mock-interviewer** | Text mock rounds; critique structure/specificity/delivery (explicitly not technical correctness); log gaps to STAR bank | conversation, debrief files | user self-assesses; pairs with human mocks |
| **ghost-job-screener** | Upgrade scout/scorer: freshness scoring, repost/evergreen detection, 24–72h apply-SLA flag | WebSearch, jobs.json | none needed (advisory flag) |
| **profile-optimizer** | Audit LinkedIn profile (pasted in) vs target roles: headline, About, skills (complete profiles ≈ 21× views) | pasted profile text | user applies edits by hand |
| **portfolio-builder** | Package 3–5 proof-of-work artifacts (JobOps itself first) into demos + one-page case studies + walkthrough scripts | filesystem, git | user approves anything published |

### Tier 3 — later / on demand

| Sub-agent | Mission | Trigger |
|---|---|---|
| **negotiation-advisor** | Comp benchmarking brief, counter-offer scripts (66–78% of negotiators win ~19% improvements) | first offer arrives |

## Skills roster (slash commands)

| Skill | What it does | Priority |
|---|---|---|
| `/jobops-intake` | The P0–P6 conversational onboarding; resumable, one phase per sitting | **now** |
| `/outreach <company> [contact]` | pathfinder → drafter for one target | **now** |
| `/follow-ups` | Weekly stale-thread sweep + drafted nudges | **now** |
| `/pipeline-review` | metrics-analyst weekly report + diagnosis | **now** |
| `/debrief` | 5-minute post-interview retro → STAR bank + metrics + positioning notes | **now** (trivial) |
| `/interview-prep <company>` | Prep pack for a scheduled interview | next |
| `/mock-interview <company> <round>` | Run a mock round + critique | next |
| `/profile-audit` | LinkedIn profile review | next |
| `/negotiate <offer>` | Negotiation brief | later |

`/jobops-daily` gains two steps: referral-pathfinder runs on every newly
qualified job, and claims-auditor gates every draft package.

## Tools / MCP & data stores

**Connect (off the shelf):**
- Google Workspace MCP (Gmail *drafts only*, Calendar, Sheets) — powers
  outreach-drafter, followup-manager, metrics export. Drafts satisfy the
  human-sends invariant.
- python-jobspy as a scout supplement — Indeed/Google backends only;
  LinkedIn backend is rate-limited and fragile.

**Connect later, with caution:** linkedin-mcp-server (read-only, low volume —
ToS exposure); Playwright ATS form *pre-fill* (Greenhouse/Lever), always
human-submitted.

**Build (shared state — the context-passing fabric):**

| Store | Contents | Consumers |
|---|---|---|
| `personal/facts.yaml` | Verified-claims ledger: every metric/achievement tagged **documented / estimated / guess** with source | tailor, claims-auditor, prep-coach, outreach-drafter |
| `personal/contacts.json` | Mini-CRM: warm/dormant/target-company contacts, outreach history, next touch | pathfinder, outreach-drafter, followup-manager |
| `data/jobs.json` (extend) | Add `channel`, `outreach[]`, `followups[]`, `interviews[]` per job | followup-manager, metrics-analyst |
| `data/debriefs/` | Post-interview retros | metrics-analyst, prep-coach, intake (STAR updates) |
| `data/metrics.json` | Weekly funnel snapshots | metrics-analyst |

## The intake questionnaire (`/jobops-intake`)

Progressive-disclosure design — seven short conversations, not one form.
Each phase is resumable and writes to the profile as it goes.

| Phase | Focus | ~Questions |
|---|---|---|
| P0 | Goals & readiness — why now, direction, urgency, hours/week | 5–8 |
| P1 | Career inventory + **artifact mining** (old resumes, reviews, praise emails) | 8–12 |
| P2 | Achievement deep-dives — behavioral-event interviewing; before/after framing; "so what" laddering; proxy quantification for underselling users | 3–5 incidents |
| P3 | Positioning & candidate-market fit + a "listening tour" assignment (3 contacts) | 5–8 |
| P4 | Constraints & dealbreakers — comp floor *and* target, must-nots (late: needs trust) | 6–10 |
| P5 | Network map — "10 people who'd take your call this week" | 5–8 |
| P6 | Read-back & verification — user tags every number **documented / estimated / guess** | read-back |

**Profile v2 schema** (upgrades `profile/TEMPLATE_master_profile.md`):
identity & logistics · positioning (2–3 role families + differentiators +
candidate-market-fit hypothesis) · experience with before-state baselines ·
skills inventory (domain expertise as a first-class cluster) · STAR bank
(8–12 stories, competency-tagged) · **network map** · constraints incl.
must-nots & risk tolerance · narrative/motivation + **voice guide** ·
search state (living). The verification contract: agents may use
*documented* numbers verbatim, round *estimates* into ranges, and never use
*guesses*.

**Living profile:** post-application (log fields used), post-interview
(`/debrief` → new STAR entries, objections → positioning edits), weekly
(`/pipeline-review` proposes profile diffs the user approves).

## Success metrics

**Inputs:** tailored applications/week (by source), outreach touches/week,
informational interviews/week. **Outputs:** response rate, app→interview
rate, interviews/week, offers. **2025–26 benchmarks:** ~3% app→interview
(<2% weak · 2–5% workable · >5% strong); ~47% final-interview→offer; median
~68.5 days to first offer; referral ≈ 40 cold applications.

**Diagnosis rules:** low response → fix targeting/keywords; responses but no
interviews → fix positioning; interviews but no offers → fix prep. Segment
by channel and resume variant; one experiment at a time, 2-week stop rule.

## Anti-roadmap (evidence says skip)

- **Auto-apply / auto-send anything** — bans, 0.1–2% conversion, backlash.
- **Headless LinkedIn scraping at volume** — fragile, ToS exposure.
- **More job boards** — discovery isn't the bottleneck; conversion is.
- **ATS keyword-score optimizers** — clean parseable formatting is enough.
- **Ever-fancier cover letters** — often unread; highest AI-suspicion surface.
- **Briefing UX polish** — pleasant, zero funnel impact.

## Privacy & generalization (framework rules)

- Public repo ships schema, prompts, and a fictional example persona; real
  data lives in gitignored `personal/` + `data/` (add a pre-commit grep for
  the user's name/email as belt-and-suspenders).
- Never leaves the machine: comp floor & negotiation strategy, the network
  map (other people's PII — the most sensitive store), visa/health details,
  interviewer-named notes. Send agents the minimum profile slice per call.
- Outreach in the user's voice: no auto-send, voice guide in profile, every
  claim traces to a ledger fact, disclosure norms per target employer.

## Build order

1. **Session A — intake:** `/jobops-intake` skill + profile v2 template +
   `facts.yaml` + `contacts.json` schemas. (Everything downstream consumes
   this.)
2. **Session B — referral lane:** referral-pathfinder + outreach-drafter +
   `/outreach`; wire pathfinder into `/jobops-daily`.
3. **Session C — trust & follow-through:** claims-auditor gate in the draft
   step + followup-manager + `/follow-ups` + jobs.json field extensions.
4. **Session D — measurement:** metrics-analyst + `/pipeline-review` +
   `/debrief`; connect Sheets export if wanted.
5. **Session E — interview lane:** prep-coach + mock-interviewer +
   `/interview-prep` + `/mock-interview`.
6. **Session F — visibility:** profile-optimizer, portfolio-builder (merges
   with the planned portfolio-website session), ghost-job-screener upgrade.

## Certification tie-ins (for the case study)

- claims-auditor = a **multi-pass review pipeline** gate (D1: sequential
  review before output ships).
- referral-pathfinder → outreach-drafter = **specialist spokes** passing
  structured context through the hub — never agent-to-agent.
- facts.yaml verification tags = **structured outputs at a trust boundary**
  (D2: schemas encode business rules — "no unverified metrics" becomes data,
  not vibes).
- `/jobops-intake` phases = **checkpointed session state** (D1: resumable
  long-running work).
- Tiered tool access per sub-agent (read-only researcher vs. drafting agents)
  = **least-privilege tool design** (D2/D3).
