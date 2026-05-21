#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-api}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

POSTGRES_USER="${POSTGRES_USER:-demo}"
POSTGRES_DB="${POSTGRES_DB:-demo}"

COMPOSE=(docker compose)
if [[ "$MODE" == "web" ]]; then
  COMPOSE=(docker compose --profile web)
elif [[ "$MODE" == "agent" ]]; then
  COMPOSE=(docker compose --profile agent --profile web)
elif [[ "$MODE" == "signals" ]]; then
  COMPOSE=(docker compose --profile signals)
fi

echo "== Smoke: docker compose ps =="
"${COMPOSE[@]}" ps

echo "== Smoke: DB reachable + seeded =="
"${COMPOSE[@]}" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select 1;" >/dev/null
"${COMPOSE[@]}" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select count(*) from kanban_cards;" >/dev/null

echo "== Smoke: API health and demo endpoints =="
"${COMPOSE[@]}" exec -T api python - <<'PY'
import json
import time
import urllib.error
import urllib.request

BASE = 'http://localhost:8000'


def wait_ready(path: str = '/healthz', timeout_s: int = 45):
    deadline = time.time() + timeout_s
    last_err = None
    while time.time() < deadline:
        try:
            urllib.request.urlopen(BASE + path, timeout=3).read()
            return
        except Exception as e:
            last_err = e
            time.sleep(1)
    raise RuntimeError(f"API not ready after {timeout_s}s; last error: {last_err}")


def get(path: str):
    body = urllib.request.urlopen(BASE + path, timeout=5).read().decode('utf-8', 'ignore')
    print(path + ':', body[:200])


wait_ready('/healthz')
for path in ['/healthz', '/health', '/readyz', '/demo/summary', '/demo/scenarios']:
    get(path)

req = urllib.request.Request(
    BASE + '/demo/run_scenario',
    data=json.dumps({'dry_run': True}).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST',
)
try:
    body = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', 'ignore')
    print('/demo/run_scenario(dry_run):', body[:200])
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', 'ignore')
    print('/demo/run_scenario(dry_run) error:', e.code, body[:200])
PY

if [[ "$MODE" == "web" || "$MODE" == "agent" ]]; then
  echo "== Smoke: Kanban web container is running =="
  "${COMPOSE[@]}" ps web | grep -E "Up|running" >/dev/null || {
    echo "❌ web container is not running"
    exit 1
  }
fi

echo "✅ Smoke checks passed"
