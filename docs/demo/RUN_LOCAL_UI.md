# Run Local Kanban Dashboard / UI

This runbook is the canonical local command guide for opening the Supply Chain Kanban AI Agent in a browser.

## Prerequisites

- Docker Desktop or Docker Engine with Docker Compose
- A terminal opened at the repo root

No Node.js install is required for the current UI because `apps/web/` is served as static HTML/CSS/JavaScript through nginx.

## 1. Create local environment

```bash
cp .env.example .env
```

Use the default `.env.example` values for a local demo. Before shared/public deployment, review `DEV_MODE`, JWT verification, CORS origins, and database credentials.

## 2. Start API + database only

```bash
make demo-min
```

Open:

```text
API docs:        http://localhost:8000/docs
Health check:    http://localhost:8000/healthz
Readiness check: http://localhost:8000/readyz
```

Use this mode for backend development, API contract checks, and connector work.

## 3. Start the browser Kanban command board

```bash
make demo-web
```

Open:

```text
Kanban command board: http://localhost:8080
API docs:              http://localhost:8000/docs
Health check:          http://localhost:8000/healthz
Readiness check:       http://localhost:8000/readyz
```

This is the recommended demo mode. It starts Postgres, seeds the demo data, starts the FastAPI backend, and serves the professional Kanban UI.

## 4. Start manager-agent mode

```bash
make demo-agent
```

Open:

```text
Kanban command board: http://localhost:8080
API docs:              http://localhost:8000/docs
```

Use this mode when showing the product as a supply-chain team lead or department manager. The background agent polls signal inputs, updates Kanban risk cases, and prepares governed action recommendations.

## 5. Optional market signal monitor

Start the browser board first:

```bash
cp .env.example .env
make demo-web
```

Then start the optional signal monitor:

```bash
make demo-signals
```

Then inspect logs:

```bash
docker compose logs -f news_monitor
```

Open:

```text
Kanban command board: http://localhost:8080
News API:             http://localhost:8000/news/items?topic=memory
News alerts:          http://localhost:8000/news/alerts?topic=memory
```

For RSS-based market monitoring, use:

```bash
NEWS_MODE=rss NEWS_TOPIC=memory make demo-signals
```

Example monitored topic: AI datacenter RAM lead-time volatility, HBM shortage, server DRAM price spike, or NAND inventory leakage.

Market signals are optional. They should enrich risk cases; they should not become the main product path.

## 6. Useful commands

```bash
make status    # show containers and run smoke checks
make logs      # tail API, agent, and news monitor logs
make psql      # open Postgres shell
make seed      # re-seed demo data without full restart
make down      # stop containers, keep volumes
make reset     # stop containers and remove volumes
make clean     # remove generated caches
make test      # Python compile checks + pytest
make test-fast # pytest only
```

## 7. Browser demo checklist

1. Open `http://localhost:8080`.
2. Confirm the status pill says API is available.
3. Click **Refresh board**.
4. Select a Kanban risk case.
5. Review impact, recommended mitigation, approval narrative, receipt, transparency, and audit timeline.
6. Click **Run approval scenario** to generate a guided crisis-operations flow.
7. Use **Open API docs** to inspect the backend contract.

## 8. Common issues

### Port already in use

```bash
make down
make demo-web
```

If the port is still blocked, check local processes using ports `8000`, `8080`, or `5432`.

### UI loads but API status is failing

Check backend logs:

```bash
docker compose logs -f api
```

Then verify directly:

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
```

### Data looks stale

```bash
make seed
```

For a full clean database:

```bash
make reset
make demo-web
```

## 9. Current UI implementation

Current implementation:

```text
apps/web/public/index.html
apps/web/public/app.js
apps/web/nginx.conf
```

This is intentionally simple for demos and fast local deployment. For a stronger professional product UI, follow `docs/product/UI_FRAMEWORK_DECISION.md`.


## Verify in Python-only sandbox

```bash
make test
```

This runs `python3 scripts/run_checks.py`, which performs Python syntax compilation and pytest.


## Streamlit AI-agent debug cockpit

Run the internal debug cockpit:

```bash
pip install -r requirements-debug.txt
make debug-ui
```

Open:

```text
http://localhost:8501
```

Use this for debugging AI-agent recommendations, policy decisions, SiteTrack container evidence, ERP writeback receipts, and blockchain proof status. The Streamlit app should call FastAPI endpoints and must not bypass approval policy.

## AI-agent operating model

Detailed manager-agent and news-monitor behavior is documented in `docs/product/AI_AGENT_OPERATING_MODEL.md`.
