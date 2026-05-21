import os
from functools import lru_cache
from pathlib import Path

import yaml

from .repo_paths import repo_root


@lru_cache(maxsize=1)
def load_lifecycle_model() -> dict:
    env = os.getenv("LIFECYCLE_MODEL_PATH")
    if env:
        p = Path(env).expanduser()
    else:
        p = repo_root() / "contracts" / "lifecycle_model.yaml"
    if not p.exists():
        raise FileNotFoundError(f"Lifecycle model not found: {p}")
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def lifecycle_object(name: str) -> dict:
    model = load_lifecycle_model() or {}
    return ((model.get("objects") or {}).get(name) or {})


def allowed_transitions(name: str) -> dict:
    return lifecycle_object(name).get("allowed_transitions") or {}
