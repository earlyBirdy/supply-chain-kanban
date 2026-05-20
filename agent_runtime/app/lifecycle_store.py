import os
from functools import lru_cache
from pathlib import Path

import yaml


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    return here.parent.parent


@lru_cache(maxsize=1)
def load_lifecycle_model() -> dict:
    env = os.getenv("LIFECYCLE_MODEL_PATH")
    if env:
        p = Path(env).expanduser()
        if not p.exists():
            raise FileNotFoundError(f"Lifecycle model not found: {p}")
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    root = _repo_root()
    p = root.parent / "contracts" / "lifecycle_model.yaml"
    if not p.exists():
        raise FileNotFoundError(f"Lifecycle model not found: {p}")
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def lifecycle_object(name: str) -> dict:
    model = load_lifecycle_model() or {}
    return ((model.get("objects") or {}).get(name) or {})


def allowed_transitions(name: str) -> dict:
    return lifecycle_object(name).get("allowed_transitions") or {}
