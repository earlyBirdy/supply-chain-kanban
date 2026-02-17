import json
from functools import lru_cache
from pathlib import Path

import yaml


def _repo_root() -> Path:
    # /app/app inside container -> repo root is /app; in source tree, this file sits in agent_runtime/app.
    # We support both layouts.
    here = Path(__file__).resolve()
    # .../agent_runtime/app/ontology_store.py -> .../agent_runtime
    return here.parent.parent


@lru_cache(maxsize=1)
def load_ontology() -> dict:
    """Load ontology from contracts/ or fall back to embedded app/ontology.json."""
    # 1) Prefer contracts in the repo root (dev mode)
    root = _repo_root()
    candidates = [
        root.parent / "contracts" / "supply_chain_ontology.json",
        root.parent / "contracts" / "supply_chain_ontology.yaml",
        root / "ontology.json",
        root / "ontology.yaml",
    ]
    for p in candidates:
        if p.exists():
            if p.suffix.lower() in (".yaml", ".yml"):
                return yaml.safe_load(p.read_text(encoding="utf-8"))
            return json.loads(p.read_text(encoding="utf-8"))
    raise FileNotFoundError("Ontology not found. Expected contracts/supply_chain_ontology.{json|yaml}")


def ontology_as_yaml() -> str:
    return yaml.safe_dump(load_ontology(), sort_keys=False, allow_unicode=True)


def ontology_as_json() -> str:
    return json.dumps(load_ontology(), ensure_ascii=False, indent=2)
