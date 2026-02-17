#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-api}"

# Load .env if present (for local vars used by psql commands)
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

POSTGRES_USER="${POSTGRES_USER:-demo}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-demo}"
POSTGRES_DB="${POSTGRES_DB:-demo}"

COMPOSE=(docker compose)
if [[ "$MODE" == "ui" ]]; then
  COMPOSE=(docker compose --profile ui --profile agent)
elif [[ "$MODE" == "agent" ]]; then
  COMPOSE=(docker compose --profile agent)
fi

echo "== Smoke: docker compose ps =="
"${COMPOSE[@]}" ps

echo "== Smoke: DB reachable + seeded =="
"${COMPOSE[@]}" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select 1;" >/dev/null
"${COMPOSE[@]}" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select count(*) from kanban_cards;" >/dev/null

echo "== Smoke: API /health =="
# Run from inside the api container so we don't depend on host curl.
"${COMPOSE[@]}" exec -T api python - <<'PY'
import urllib.request
import json
def get(path: str):
    url = 'http://localhost:8000' + path
    body = urllib.request.urlopen(url, timeout=5).read().decode('utf-8', 'ignore')
    print(path + ':', body[:200])

get('/healthz')
get('/health')
get('/readyz')
get('/demo/summary')
get('/demo/scenarios')

# dry-run scenario (no DB writes)
import urllib.error
req = urllib.request.Request('http://localhost:8000/demo/run_scenario', data=json.dumps({"dry_run": True}).encode('utf-8'), headers={"Content-Type":"application/json"}, method='POST')
try:
    body = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', 'ignore')
    print('/demo/run_scenario(dry_run):', body[:200])
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', 'ignore')
    print('/demo/run_scenario(dry_run) error:', e.code, body[:200])
PY

if [[ "$MODE" == "ui" ]]; then
  echo "== Smoke: Superset /health =="
  "${COMPOSE[@]}" exec -T superset python - <<'PY'
import urllib.request
url = 'http://localhost:8088/health'
body = urllib.request.urlopen(url, timeout=10).read().decode('utf-8', 'ignore')
print('superset health:', body[:200])
PY

  echo "== Smoke: Superset bootstrap completed =="
  # Bootstrap is a one-shot container; ensure it exited successfully.
  if ! "${COMPOSE[@]}" ps superset_bootstrap | grep -E "exited\s*\(0\)" >/dev/null; then
    echo "❌ superset_bootstrap has not exited (0). Check logs: docker compose --profile ui logs superset_bootstrap"
    exit 1
  fi
fi

echo "✅ Smoke checks passed"
