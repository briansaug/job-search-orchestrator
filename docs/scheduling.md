# Daily scheduled run (macOS launchd)

The Claude Code surface runs unattended each morning on a Claude
subscription — no API key in the environment (an exported
`ANTHROPIC_API_KEY` would silently take precedence over subscription auth).

`~/Library/LaunchAgents/com.brianbruner.jobops-daily.plist` runs, daily at
8:00 AM (or on next wake if the machine was asleep):

```sh
cd /Users/brianbruner/job-search-orchestrator && \
  claude -p "/jobops-daily" --model claude-sonnet-5 \
  --permission-mode acceptEdits >> data/cron.log 2>&1
```

The model is pinned to match the pipeline default (`jobops/config.py`).
To run the daily on Opus 4.8 instead, change the flag to
`--model claude-opus-4-8` and re-bootstrap the job (below), or launch a
one-off from the cockpit's model picker.

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

## Always-on cockpit (launchd)

A second LaunchAgent keeps the web cockpit permanently available at
<http://127.0.0.1:8765> (localhost-only — private to this Mac):

`~/Library/LaunchAgents/com.brianbruner.jobops-cockpit.plist` runs
`.venv/bin/python -m jobops dashboard --no-browser` at login and restarts
it if it exits (`KeepAlive`), logging to `data/cockpit.log`.

```sh
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.brianbruner.jobops-cockpit.plist   # enable
launchctl bootout   gui/$(id -u)/com.brianbruner.jobops-cockpit                                 # disable
launchctl kickstart -k gui/$(id -u)/com.brianbruner.jobops-cockpit                              # restart (e.g. after code changes)
```

Restart it after pulling cockpit code changes — the running server serves
`dashboard.html` fresh per request, but `dashboard.py` changes need the
restart.
