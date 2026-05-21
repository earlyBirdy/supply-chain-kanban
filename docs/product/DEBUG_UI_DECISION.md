# Debug UI Decision: Streamlit AI-Agent Cockpit + Grafana Observability

## Decision

Use **Streamlit** as the AI-agent debug cockpit for this repo.

```text
Primary operator UI:       apps/web/public Kanban browser UI
AI-agent debug cockpit:    Streamlit under apps/debug_ui/
Observability dashboard:   Grafana later, after metrics exist
Production UI upgrade:     React + Vite + TypeScript later
```

Do not use one UI tool for every job.

## Why Streamlit is the best next tool for the AI agent

Streamlit is the best near-term tool because this project is Python/FastAPI-first and the team needs to debug agent behavior quickly. It lets us inspect the manager-agent loop without building a full frontend app first.

Use Streamlit for:

```text
agent recommendation traces
Kanban risk-case inspection
approval-policy decisions
SiteTrack container-event payloads
ERP/WMS/TMS writeback receipts
blockchain evidence-anchor status
scenario replay and debugging
```

Do **not** use Streamlit as the long-term polished SaaS UI. Keep the main operator experience in the browser Kanban UI, then migrate it to React/Vite when the workflow becomes more complex.

## Tool split

| Tool | Role | Use now? |
|---|---|---|
| Static Kanban UI | human operator / manager workflow | yes |
| Streamlit | AI-agent debug cockpit | yes |
| Grafana | metrics, logs, connector health, ledger-anchor health | later |
| React + Vite | production-grade Kanban/control-plane UI | later |

## Added app

```text
apps/debug_ui/streamlit_app.py
requirements-debug.txt
```

Run:

```bash
pip install -r requirements-debug.txt
make debug-ui
```

Open:

```text
http://localhost:8501
```

Optional API override:

```bash
API_BASE_URL=http://localhost:8000 make debug-ui
```

## Streamlit data-access rule

The debug cockpit should call FastAPI endpoints first, not private database tables.

```text
Good: Streamlit -> FastAPI -> service/database
Avoid: Streamlit -> direct private DB reads/writes
```

This keeps the debug tool aligned with production contracts and prevents it from becoming a bypass around approval/governance rules.

## Write-safety rule

Streamlit may show debug and trace data. It must not bypass approval policy.

Allowed:

```text
read cases
read recommendations
read audit events
read execution receipts
read blockchain proof status
read SiteTrack evidence payloads
run dry-run simulations
```

Not allowed without explicit governed API support:

```text
approve actions directly
execute ERP writebacks directly
edit ledger events directly
mutate SiteTrack evidence directly
```

## Grafana later

Grafana should be added only after the API exports real metrics.

Useful Grafana panels:

```text
API latency and error rate
/healthz and /readyz status
case creation rate
approval queue depth
ERP connector success/failure
SiteTrack event freshness
blockchain ledger-anchor success/failure
background agent loop duration
```

Recommended future tree:

```text
infra/grafana/
  dashboards/
    supply_chain_agent_health.json
    connector_health.json
    blockchain_evidence_health.json
  provisioning/
```

## Acceptance criteria

```text
make debug-ui starts Streamlit on :8501
Streamlit reads FastAPI endpoints
case lifecycle is visible
AI recommendations are visible
execution receipts/audit timeline are visible
future SiteTrack and blockchain panels can be added without changing the main operator UI
```
