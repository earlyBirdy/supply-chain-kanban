import os
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml

import hashlib
import json


# Hot-reload cache (mtime-based)
_cached: Tuple[float, Dict[str, Any]] | None = None


def _repo_root() -> Path:
    # .../agent_runtime/app/policy_store.py -> .../agent_runtime
    here = Path(__file__).resolve()
    return here.parent.parent


def _policy_path() -> Path:
    # Allow override for deployments
    env = os.getenv("GOV_POLICY_PATH")
    if env:
        return Path(env).expanduser()
    root = _repo_root()
    # Prefer governance/policy.yaml at repo root (dev mode)
    candidates = [
        root.parent / "governance" / "policy.yaml",
        root / "governance" / "policy.yaml",
    ]
    for p in candidates:
        if p.exists():
            return p
    # Fall back to embedded default (should exist in source tree)
    return root.parent / "governance" / "policy.yaml"


def load_policy() -> Dict[str, Any]:
    """Load the effective governance policy with hot-reload (mtime-based).

    This is intentionally light-weight: any request that needs policy calls this function.
    """
    global _cached
    p = _policy_path()
    if not p.exists():
        raise FileNotFoundError(f"Governance policy not found: {p}")

    mtime = p.stat().st_mtime
    if _cached is None or _cached[0] != mtime:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        _cached = (mtime, data)
    return _cached[1]


def policy_as_yaml() -> str:
    return yaml.safe_dump(load_policy(), sort_keys=False, allow_unicode=True)


def policy_path_str() -> str:
    return str(_policy_path())


def save_policy(policy: Dict[str, Any]) -> None:
    """Persist governance policy to the effective policy.yaml and invalidate cache.

    Only intended for development workflows (see /governance/policy endpoints).
    Uses atomic write to avoid partial files.
    """
    global _cached
    p = _policy_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    data = yaml.safe_dump(policy, sort_keys=False, allow_unicode=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(p)
    _cached = None



def policy_revision(policy: Dict[str, Any] | None = None) -> int:
    p = policy if policy is not None else load_policy()
    try:
        return int(p.get("revision", 0))
    except Exception:
        return 0


def policy_etag(policy: Dict[str, Any] | None = None) -> str:
    """Stable ETag for the policy content (sha256 of canonical JSON)."""
    p = policy if policy is not None else load_policy()
    s = json.dumps(p, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
