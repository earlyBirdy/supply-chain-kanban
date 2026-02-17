#!/usr/bin/env bash
set -euo pipefail

# Clean build/test artifacts that should never ship in a repo zip.

rm -rf .pytest_cache || true

find . -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete 2>/dev/null || true
find . -type f -name '*.pyo' -delete 2>/dev/null || true

# Editor / backup artifacts
find . -type f -name '*.bak' -delete 2>/dev/null || true
find . -type f -name '*.bak*' -delete 2>/dev/null || true
find . -type f -name '*~' -delete 2>/dev/null || true

# OS junk
find . -type f -name '.DS_Store' -delete 2>/dev/null || true

# Python tooling caches
rm -rf .ruff_cache .mypy_cache .coverage htmlcov || true

# Keep the repo root clean
printf '✅ Clean complete (pycache/pyc/bak/test caches removed)\n'
