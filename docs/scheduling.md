# Daily scheduled run (macOS launchd)

The Claude Code surface runs unattended each morning on a Claude
subscription — no API key in the environment (an exported
`ANTHROPIC_API_KEY` would silently take precedence over subscription auth).

`~/Library/LaunchAgents/com.brianbruner.jobops-daily.plist` runs, daily at
8:00 AM (or on next wake if the machine was asleep):

```sh
cd /Users/brianbruner/job-search-orchestrator && \
  claude -p "/jobops-daily" --permission-mode acceptEdits >> data/cron.log 2>&1
```

Headless permissions are pre-granted in `.claude/settings.json`: WebSearch,
and writes confined to `data/`. The profile, config, and source directories
are deny-listed — the scheduled agent can add jobs and drafts but cannot
change its own rubric or the candidate profile.

Manage the job:

```sh
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.brianbruner.jobops-daily.plist   # enable
launchctl bootout   gui/$(id -u)/com.brianbruner.jobops-daily                                # disable
launchctl kickstart gui/$(id -u)/com.brianbruner.jobops-daily                                # run now
tail -f data/cron.log                                                                        # watch a run
```

Each run ends by writing `data/BRIEFING.md` — the morning read: new
postings, scores, drafts awaiting review.
