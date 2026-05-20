from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    return here.parent.parent


@lru_cache(maxsize=1)
def load_demo_experience_pack() -> dict:
    env = os.getenv("DEMO_EXPERIENCE_PACK_PATH")
    if env:
        p = Path(env).expanduser()
    else:
        p = _repo_root().parent / "contracts" / "demo_experience_pack.yaml"
    if not p.exists():
        raise FileNotFoundError(f"Demo experience pack not found: {p}")
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def branding_options() -> dict:
    return load_demo_experience_pack().get("brands") or {}


def seed_pack_catalog() -> dict:
    return load_demo_experience_pack().get("seed_packs") or {}


def guided_scripts() -> dict:
    return load_demo_experience_pack().get("demo_scripts") or {}
