from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Find the source repo root from the runtime package location.

    Local tests run with PYTHONPATH=apps/api, while containers may mount
    contracts/data/governance into fixed paths. This helper keeps source-tree
    fallback predictable after the professional repo-tree rearrangement.
    """
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "contracts").is_dir() and (parent / "operations").is_dir():
            return parent
    # Source-tree fallback: <repo>/apps/api/app/repo_paths.py
    if len(here.parents) >= 4:
        return here.parents[3]
    return here.parent
