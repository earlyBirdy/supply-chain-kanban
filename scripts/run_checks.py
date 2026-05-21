#!/usr/bin/env python3
"""Repository quality gate that uses only Python + pytest.

This is the repo minimum gate: standard-library Python syntax compilation plus pytest.
It intentionally avoids external lint dependencies so it can run in constrained sandboxes.
"""
from __future__ import annotations

import compileall
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PYTHONPATH = str(ROOT / "apps" / "api")


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    print("$ " + " ".join(cmd), flush=True)
    completed = subprocess.run(cmd, cwd=ROOT, env=env)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def compile_python_tree(path: pathlib.Path) -> None:
    print(f"==> Python syntax compile: {path.relative_to(ROOT)}", flush=True)
    ok = compileall.compile_dir(
        str(path),
        quiet=1,
        force=False,
        maxlevels=20,
    )
    if not ok:
        raise SystemExit(1)


def main() -> None:
    compile_python_tree(ROOT / "apps" / "api")
    compile_python_tree(ROOT / "tests")

    env = os.environ.copy()
    env["PYTHONPATH"] = PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
    run([sys.executable, "-m", "pytest", "-q"], env=env)
    print("✅ Python quality gate passed", flush=True)


if __name__ == "__main__":
    main()
