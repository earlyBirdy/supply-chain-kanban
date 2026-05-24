from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_demo_targets_use_safe_compose_wrapper() -> None:
    makefile = (ROOT / "Makefile").read_text()
    wrapper = ROOT / "scripts" / "compose_up_safe.sh"

    assert wrapper.exists()
    assert "COMPOSE_PARALLEL_LIMIT" in wrapper.read_text()
    assert "failed to set up container networking" in wrapper.read_text()
    assert "./scripts/compose_up_safe.sh --profile agent --profile web up -d --build" in makefile
    assert "docker compose down --remove-orphans -v || true" in makefile
