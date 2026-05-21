# AI Agents Explained

The repo currently supports two agent paths:

1. **Manager-agent path** — runs like a supply-chain team lead or department manager.
2. **News/market-signal path** — monitors external supply risk signals such as AI datacenter RAM lead-time volatility.

Canonical detailed doc: `docs/product/AI_AGENT_OPERATING_MODEL.md`.

## Run the manager-agent path

```bash
cp .env.example .env
make demo-agent
```

Open:

```text
Kanban command board: http://localhost:8080
API docs:              http://localhost:8000/docs
```

The manager-agent watches operating signals, updates Kanban risk cases, recommends mitigations, routes approvals, executes governed writebacks, and stores audit evidence.

## Run the news/market-signal path

```bash
cp .env.example .env
make demo-web
make demo-signals
```

Open:

```text
Kanban command board: http://localhost:8080
News API:             http://localhost:8000/news/items?topic=memory
```

Example risk:

```text
AI datacenter RAM lead-time volatility
  -> memory supply risk signal
  -> impacted server BOM / open orders
  -> Kanban risk case
  -> recommendation: reserve allocation, adjust supplier split, approve premium buy if needed
  -> governed writeback + audit evidence
```

## What agents do

```text
Monitor signals
Detect constraints
Create/update risk cases
Run scenarios
Recommend actions
Route approvals
Prepare governed writebacks
Attach receipts and audit evidence
```

## What agents do not do

```text
Do not self-authorize contracts.
Do not bypass approval policy.
Do not write directly into ERP/WMS/TMS outside governed connectors.
Do not treat blockchain as a validator for bad source data.
Do not learn or auto-change policy without governance.
```

## Tool split

```text
Browser Kanban UI  - main team-lead / manager workflow
Streamlit          - AI-agent debug cockpit
Grafana            - later observability, not the main operations UI
```
