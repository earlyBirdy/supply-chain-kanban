#!/usr/bin/env bash
set -euo pipefail

cat <<'TXT'

=== Professional demo checklist ===

1) Services
   - Kanban board:  http://localhost:8080
   - API docs:      http://localhost:8000/docs
   - API liveness:  GET /healthz
   - API readiness: GET /readyz

2) Manager-agent flow to show
   - Signal creates or updates a Kanban risk case
   - Case explains impact, evidence, SLA, owner, and recommendation
   - Approval gate blocks unsafe writeback
   - Approved action executes through a governed connector
   - Receipt and audit timeline prove what happened

3) Quick endpoints
   - GET  /operator/summary
   - GET  /operator/board
   - GET  /audit/recent?limit=20
   - GET  /governance/policy
   - GET  /demo/scenarios
   - POST /demo/run_scenario

4) Reset for re-demo (DEV_MODE=1 only)
   - POST /demo/reset

Tip: include X-Request-Id in requests; it will echo back and appear in logs + audit.
TXT
