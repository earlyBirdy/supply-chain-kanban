from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    return here.parent.parent


@lru_cache(maxsize=1)
def load_demo_story_pack() -> dict:
    env = os.getenv("DEMO_STORY_PACK_PATH")
    if env:
        p = Path(env).expanduser()
    else:
        p = _repo_root().parent / "contracts" / "demo_story_pack.yaml"
    if not p.exists():
        raise FileNotFoundError(f"Demo story pack not found: {p}")
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def story_personas() -> dict:
    return (load_demo_story_pack().get("personas") or {})


def customer_themes() -> dict:
    return (load_demo_story_pack().get("customer_themes") or {})
