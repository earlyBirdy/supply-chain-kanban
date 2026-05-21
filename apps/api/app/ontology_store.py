import json
import os
from functools import lru_cache
from pathlib import Path

import yaml

from .repo_paths import repo_root


@lru_cache(maxsize=1)
def load_ontology() -> dict:
    """Load ontology from the canonical contracts location only."""
    env = os.getenv("ONTOLOGY_PATH")
    if env:
        p = Path(env).expanduser()
        if not p.exists():
            raise FileNotFoundError(f"Ontology not found: {p}")
        if p.suffix.lower() in (".yaml", ".yml"):
            return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return json.loads(p.read_text(encoding="utf-8"))

    candidates = [
        repo_root() / "contracts" / "supply_chain_ontology.yaml",
        repo_root() / "contracts" / "supply_chain_ontology.json",
    ]
    for p in candidates:
        if p.exists():
            if p.suffix.lower() in (".yaml", ".yml"):
                return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            return json.loads(p.read_text(encoding="utf-8"))
    raise FileNotFoundError("Ontology not found. Expected contracts/supply_chain_ontology.{yaml|json}")


def ontology_as_yaml() -> str:
    return yaml.safe_dump(load_ontology(), sort_keys=False, allow_unicode=True)


def ontology_as_json() -> str:
    return json.dumps(load_ontology(), ensure_ascii=False, indent=2)
