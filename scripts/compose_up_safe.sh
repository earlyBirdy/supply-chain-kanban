#!/usr/bin/env bash
set -euo pipefail

# Docker Desktop can occasionally return "network ... not found" when a fresh
# `down -v` is followed by a multi-profile `up --build` with several containers
# starting in parallel. Serialize starts and retry once with a clean compose
# network so `make demo-agent` remains deterministic for local demos.

if [[ $# -lt 1 ]]; then
  echo "usage: scripts/compose_up_safe.sh <compose args...>" >&2
  exit 64
fi

LOG_FILE="${TMPDIR:-/tmp}/supply-chain-kanban-compose-up.log"
: >"$LOG_FILE"

run_up() {
  COMPOSE_PARALLEL_LIMIT="${COMPOSE_PARALLEL_LIMIT:-1}" docker compose "$@" 2>&1 | tee "$LOG_FILE"
}

if run_up "$@"; then
  exit 0
fi

if grep -Eq "network .* not found|failed to set up container networking" "$LOG_FILE"; then
  echo "⚠️ Docker compose network race detected; retrying once with a clean project network..." >&2
  docker compose down --remove-orphans || true
  sleep 2
  run_up "$@"
  exit $?
fi

exit 1
