"""Command-line entry points — the orchestrator's control panel.

  python -m jobops scout            find new jobs (all scout agents)
  python -m jobops add              add a job by hand (e.g. from LinkedIn)
  python -m jobops process          score -> gate -> research -> draft
  python -m jobops status           show the pipeline dashboard
  python -m jobops dashboard        local web cockpit (live pipeline view + run buttons)
  python -m jobops mark ID STAGE    record manual outcomes (submitted, interview...)
  python -m jobops selftest         one cheap end-to-end scorer call
"""

import argparse
import sys

from . import tracker
from .config import load_master_profile, load_search_profile


def cmd_scout(_args):
    from .agents.scout import run_scouts
    jobs = tracker.load_jobs()
    found = run_scouts()
    new = 0
    for f in found:
        job = tracker.add_job(jobs, f["company"], f["title"], f.get("url", ""),
                              f.get("summary", ""), f.get("source", "scout"))
        if job:
            new += 1
    tracker.save_jobs(jobs)
    print(f"\nScouting done: {len(found)} found, {new} new (rest were already tracked).")
    print("Next: python -m jobops process")


def cmd_add(args):
    jobs = tracker.load_jobs()
    print("Paste the job description (finish with Ctrl-D on an empty line):")
    description = sys.stdin.read().strip()
    job = tracker.add_job(jobs, args.company, args.title, args.url or "",
                          description, source="manual")
    tracker.save_jobs(jobs)
    print(f"Added: {job['id']}" if job else "Already tracked — skipped.")


def cmd_process(args):
    from .agents.researcher import research_company
    from .agents.scorer import gate, score_job
    from .agents.tailor import draft_package

    profile_text = load_master_profile()
    limit = args.limit or load_search_profile()["pipeline"]["max_jobs_per_process_run"]
    jobs = tracker.load_jobs()

    todo = [j for j in jobs if j["stage"] == "scouted"][:limit]
    if not todo:
        print("Nothing in 'scouted'. Run `scout` or `add` first.")
        return

    for job in todo:
        print(f"\n=== {job['company']} — {job['title']} ===")
        detail = score_job(job, profile_text)
        job["score"], job["score_detail"] = detail["score"], detail
        stage = gate(detail["score"])
        tracker.set_stage(job, stage, f"score {detail['score']}/10")
        print(f"  score: {detail['score']}/10 → {stage}")
        print(f"  rationale: {detail['rationale'][:200]}")
        tracker.save_jobs(jobs)  # checkpoint after every expensive step

        if stage != "qualified":
            continue

        print("  researching company...")
        job["research"] = research_company(job)
        tracker.set_stage(job, "researched")
        tracker.save_jobs(jobs)

        print("  drafting application package...")
        paths = draft_package(job, profile_text, job["research"])
        tracker.set_stage(job, "drafted")
        tracker.save_jobs(jobs)
        print("  drafts ready for YOUR review:")
        for p in paths:
            print(f"    {p}")

    tracker.dashboard(jobs)
    print("\nDashboard updated: data/STATUS.md")


def cmd_status(_args):
    print(tracker.dashboard(tracker.load_jobs()))


def cmd_dashboard(args):
    from .dashboard import serve
    serve(port=args.port, open_browser=not args.no_browser)


def cmd_mark(args):
    jobs = tracker.load_jobs()
    job = next((j for j in jobs if j["id"] == args.id), None)
    if not job:
        print(f"No job with id '{args.id}'. Run `status` to see ids.")
        return
    tracker.set_stage(job, args.stage, args.note or "manual")
    tracker.save_jobs(jobs)
    print(f"{job['company']} — {job['title']} → {args.stage}")


def cmd_selftest(_args):
    """One scorer call on a fabricated posting — verifies key, model, schema."""
    from .agents.scorer import gate, score_job
    sample = {
        "company": "KUNGFU.AI",
        "title": "AI Solutions Consultant",
        "location": "Austin, TX (hybrid)",
        "summary": "Client-facing role scoping and delivering LLM solutions for "
                   "enterprise clients. Requires experience with Claude or GPT "
                   "APIs, agent architectures, and translating business problems "
                   "into AI systems. Consulting or client-service background valued.",
    }
    detail = score_job(sample, load_master_profile())
    print(f"score: {detail['score']}/10 → {gate(detail['score'])}")
    print(f"location_fit: {detail['location_fit']}")
    print(f"angle: {detail['angle']}")
    print(f"rationale: {detail['rationale']}")
    print("\nSelf-test passed: API key, model, and structured output all working.")


def main():
    parser = argparse.ArgumentParser(prog="jobops")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scout").set_defaults(func=cmd_scout)

    p_add = sub.add_parser("add")
    p_add.add_argument("company")
    p_add.add_argument("title")
    p_add.add_argument("--url", default="")
    p_add.set_defaults(func=cmd_add)

    p_proc = sub.add_parser("process")
    p_proc.add_argument("--limit", type=int, default=None)
    p_proc.set_defaults(func=cmd_process)

    sub.add_parser("status").set_defaults(func=cmd_status)

    p_dash = sub.add_parser("dashboard")
    p_dash.add_argument("--port", type=int, default=8765)
    p_dash.add_argument("--no-browser", action="store_true")
    p_dash.set_defaults(func=cmd_dashboard)

    p_mark = sub.add_parser("mark")
    p_mark.add_argument("id")
    p_mark.add_argument("stage", choices=tracker.STAGES)
    p_mark.add_argument("--note", default="")
    p_mark.set_defaults(func=cmd_mark)

    sub.add_parser("selftest").set_defaults(func=cmd_selftest)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
