"""Shared configuration: paths, model choice, and YAML config loaders."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# Cost-balanced default; override per-run with JOBOPS_MODEL=claude-opus-4-8 etc.
MODEL = os.environ.get("JOBOPS_MODEL", "claude-sonnet-4-6")

CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
DRAFTS_DIR = DATA_DIR / "drafts"
JOBS_FILE = DATA_DIR / "jobs.json"
PROFILE_FILE = ROOT / "profile" / "master_profile.md"


def load_search_profile() -> dict:
    with open(CONFIG_DIR / "search_profile.yaml") as f:
        return yaml.safe_load(f)


def load_target_companies() -> dict:
    with open(CONFIG_DIR / "target_companies.yaml") as f:
        return yaml.safe_load(f)


def load_master_profile() -> str:
    if not PROFILE_FILE.exists():
        raise FileNotFoundError(
            "profile/master_profile.md not found — copy the template and fill it in."
        )
    return PROFILE_FILE.read_text()
