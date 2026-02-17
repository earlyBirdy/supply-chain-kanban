#!/usr/bin/env bash
set -euo pipefail

cat <<'TXT'

=== Demo checklist ===

1) Services
   - API docs:      http://localhost:8000/docs
   - API liveness:  GET /healthz
   - API readiness: GET /readyz
   - Superset UI:   http://localhost:8088  (if started with make demo-ui / demo-all)

2) Quick endpoints to show
   - GET  /demo/summary         (counts + policy revision)
   - GET  /audit/recent?limit=20
   - GET  /governance/policy    (effective policy)
   - GET  /demo/scenarios      (list canned stories)
   - POST /demo/run_scenario   (generate a full narrative)

3) Action demo flow
   - Pick a card from /demo/summary (or /objects/cards if you have it)
   - POST /actions/execute with Idempotency-Key
   - Show audit entry created in /audit/recent

4) Reset for re-demo (DEV_MODE=1 only)
   - POST /demo/reset

Tip: include X-Request-Id in requests; it will echo back and appear in logs + audit.
TXT
