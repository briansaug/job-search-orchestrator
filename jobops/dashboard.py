"""Local web cockpit — watch the pipeline live, read drafts, trigger runs.

    .venv/bin/python -m jobops dashboard              # http://127.0.0.1:8765
    .venv/bin/python -m jobops dashboard --port 9000 --no-browser

Read-mostly by design: the UI reads the same state files the agents write
(data/jobs.json, data/BRIEFING.md, data/drafts/) and polls for changes, so
a running pipeline animates as jobs change stage. Its only writes are the
two things a human could already do in a terminal: launch a whitelisted
pipeline run as a subprocess, and record a manual outcome (`mark`). It
binds to localhost only and never submits anything anywhere.

Billing note: the `daily` mode spawns the Claude Code surface, which must
run on subscription auth — an inherited ANTHROPIC_API_KEY would silently
switch it to API billing (see docs/scheduling.md), so it is stripped from
that subprocess's environment.
"""

import json
import os
import shutil
import subprocess
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import tracker
from .config import DATA_DIR, DRAFTS_DIR, JOBS_FILE, ROOT, load_search_profile

HTML_FILE = Path(__file__).parent / "dashboard.html"
RUN_LOG = DATA_DIR / "dashboard_run.log"
INTAKE_STATE = ROOT / "profile" / "intake_state.json"
BRIEFING = DATA_DIR / "BRIEFING.md"

# Stages a human may record from the UI — outcomes only, mirroring `jobops
# mark`. Pipeline stages (qualified, drafted, ...) stay agent/gate-owned.
MARK_STAGES = ["submitted", "response", "interview", "offer", "closed"]


def _run_modes() -> dict[str, list[str]]:
    py = str(ROOT / ".venv" / "bin" / "python")
    return {
        "scout": [py, "-m", "jobops", "scout"],
        "process": [py, "-m", "jobops", "process"],
        "daily": ["claude", "-p", "/jobops-daily", "--permission-mode",
                  "acceptEdits"],
    }


class RunManager:
    """At most one pipeline subprocess at a time, output tee'd to RUN_LOG."""

    def __init__(self):
        self.proc = None
        self.mode = None
        self.started = None
        self.last_exit = None
        self.last_mode = None
        self.lock = threading.Lock()

    def active(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def start(self, mode: str) -> tuple[bool, str]:
        cmds = _run_modes()
        if mode not in cmds:
            return False, f"unknown mode '{mode}'"
        with self.lock:
            if self.active():
                return False, f"a '{self.mode}' run is already active"
            env = os.environ.copy()
            if mode == "daily":
                if shutil.which("claude") is None:
                    return False, "claude CLI not found on PATH"
                env.pop("ANTHROPIC_API_KEY", None)  # keep subscription auth
            DATA_DIR.mkdir(exist_ok=True)
            fh = open(RUN_LOG, "wb")
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fh.write(f"[{stamp}] starting '{mode}': {' '.join(cmds[mode])}\n"
                     .encode())
            fh.flush()
            try:
                self.proc = subprocess.Popen(
                    cmds[mode], cwd=ROOT, env=env, stdout=fh,
                    stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
            except OSError as e:
                fh.write(f"failed to start: {e}\n".encode())
                fh.close()
                return False, f"failed to start: {e}"
            self.mode = mode
            self.started = datetime.now(timezone.utc).isoformat()
            threading.Thread(target=self._watch, args=(self.proc, fh, mode),
                             daemon=True).start()
            return True, "started"

    def _watch(self, proc, fh, mode):
        code = proc.wait()
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fh.write(f"\n[{stamp}] '{mode}' finished with exit code {code}\n"
                 .encode())
        fh.close()
        self.last_exit, self.last_mode = code, mode

    def stop(self) -> tuple[bool, str]:
        with self.lock:
            if not self.active():
                return False, "nothing is running"
            self.proc.terminate()
            return True, "terminate signal sent"

    def snapshot(self) -> dict:
        return {
            "active": self.active(),
            "mode": self.mode if self.active() else None,
            "started": self.started if self.active() else None,
            "last_exit": self.last_exit,
            "last_mode": self.last_mode,
            "log_bytes": RUN_LOG.stat().st_size if RUN_LOG.exists() else 0,
        }


RUNS = RunManager()
_jobs_cache: list = []


def _load_jobs_safe() -> list:
    """jobs.json is rewritten between checkpoints — never crash on a torn read."""
    global _jobs_cache
    try:
        if JOBS_FILE.exists():
            _jobs_cache = json.loads(JOBS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        pass  # keep serving the last good snapshot
    return _jobs_cache


def _drafts_index(jobs: list) -> dict:
    out = {}
    for job in jobs:
        d = DRAFTS_DIR / job["id"]
        if not d.is_dir():
            continue
        files = []
        for f in sorted(d.glob("*.md")):
            try:
                files.append({"name": f.name, "content": f.read_text()})
            except OSError:
                continue
        if files:
            out[job["id"]] = files
    return out


def _state() -> dict:
    jobs = _load_jobs_safe()
    try:
        pipeline = load_search_profile().get("pipeline", {})
        gates = {"qualified": pipeline.get("score_gate_qualified", 7),
                 "borderline": pipeline.get("score_gate_borderline", 5)}
    except Exception:
        gates = {"qualified": 7, "borderline": 5}
    intake = None
    if INTAKE_STATE.exists():
        try:
            intake = json.loads(INTAKE_STATE.read_text())
        except (json.JSONDecodeError, OSError):
            intake = None
    briefing, briefing_mtime = None, None
    if BRIEFING.exists():
        briefing = BRIEFING.read_text()
        briefing_mtime = datetime.fromtimestamp(
            BRIEFING.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stages": tracker.STAGES,
        "mark_stages": MARK_STAGES,
        "gates": gates,
        "jobs": jobs,
        "drafts": _drafts_index(jobs),
        "briefing": briefing,
        "briefing_mtime": briefing_mtime,
        "intake": intake,
        "run": RUNS.snapshot(),
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the terminal quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj).encode(), "application/json")

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            return {}

    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path == "/":
            self._send(200, HTML_FILE.read_bytes(), "text/html; charset=utf-8")
        elif path == "/api/state":
            self._json(_state())
        elif path == "/api/log":
            params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
            offset = max(0, int(params.get("offset", "0") or 0))
            text, new_offset = "", offset
            if RUN_LOG.exists():
                size = RUN_LOG.stat().st_size
                if offset > size:  # log was restarted
                    offset = 0
                with open(RUN_LOG, "rb") as f:
                    f.seek(offset)
                    chunk = f.read(65536)
                text = chunk.decode(errors="replace")
                new_offset = offset + len(chunk)
            self._json({"text": text, "offset": new_offset})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/api/run":
            ok, msg = RUNS.start(str(self._read_body().get("mode", "")))
            self._json({"ok": ok, "message": msg}, 200 if ok else 409)
        elif self.path == "/api/stop":
            ok, msg = RUNS.stop()
            self._json({"ok": ok, "message": msg}, 200 if ok else 409)
        elif self.path == "/api/mark":
            body = self._read_body()
            job_id, stage = body.get("id"), body.get("stage")
            if stage not in MARK_STAGES:
                self._json({"ok": False,
                            "message": f"stage must be one of {MARK_STAGES}"},
                           400)
                return
            jobs = tracker.load_jobs()
            job = next((j for j in jobs if j["id"] == job_id), None)
            if not job:
                self._json({"ok": False, "message": f"no job '{job_id}'"}, 404)
                return
            tracker.set_stage(job, stage, body.get("note") or "via dashboard")
            tracker.save_jobs(jobs)
            self._json({"ok": True, "message": f"{job['company']} → {stage}"})
        else:
            self._json({"error": "not found"}, 404)


def serve(port: int = 8765, open_browser: bool = True):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}"
    print(f"JobOps cockpit: {url}  (Ctrl-C to stop)")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCockpit stopped.")
