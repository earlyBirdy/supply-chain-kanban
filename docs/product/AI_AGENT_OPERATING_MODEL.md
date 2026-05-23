# AI Agent Operating Model

This repo has two practical AI-agent operating modes:

1. **Supply-chain team lead / department manager mode**
2. **Market/news signal monitoring mode**

Both modes feed the same Kanban command board. The important rule is that the AI agent does not replace ERP, WMS, TMS, SiteTrack, or human approval. It watches signals, opens risk cases, recommends action, routes approvals, and writes back only through governed connectors.

---

## 1. Manager-agent mode: runs like a supply-chain team lead

Run command:

```bash
cp .env.example .env
make demo-agent
```

Open:

```text
Kanban command board: http://localhost:8080
API docs:              http://localhost:8000/docs
```

Use this mode when showing the product as a supply-chain team lead or department manager.

### Supply-chain leader responsibilities

In manager-agent mode, the AI agent drives the daily operating board like a supply-chain team lead. It should continuously check:

```text
Forecast accuracy and demand-change risk
Inventory alignment with plan, safety stock, open orders, and constrained resources
Partner performance metrics: OTIF, yield, scrap, efficiency, responsiveness
Integrated operating-plan gaps across demand planning, finance, and operations
Approval blockers, execution aging, receipts, and audit/evidence completeness
```

The agent should convert these checks into Kanban cases only when there is a management action to take: expedite, reallocate, adjust supplier split, approve premium buy, hold/release inventory, change production priority, update promise date, or request cross-functional review.

### What the agent does

```text
ERP / WMS / MES / SiteTrack signals
  -> normalize into operating signals
  -> compute risk score and confidence
  -> create or update a Kanban risk case
  -> estimate impact: supply gap, revenue at risk, cost impact, service impact
  -> recommend mitigation actions
  -> route high-risk actions to approval
  -> execute only after policy allows it
  -> store receipt and audit evidence
```

### Current implementation map

```text
apps/api/app/ingest.py                 CSV/sample ERP, WMS, MES ingest
apps/api/app/signals.py                latest market and supplier signal loaders
apps/api/app/risk_model.py             risk score / confidence / lead-time factor
apps/api/app/scenarios.py              scenario simulation: base, supply shock, price shock, double hit
apps/api/app/approval.py               approval policy resolution
apps/api/app/execution.py              governed execution path
apps/api/app/audit.py                  audit trail and request-id evidence
apps/api/app/connectors/               ERP / supplier / ticketing writeback stubs
apps/api/app/api/routers/operator.py   Kanban command-board API
apps/web/public/                       browser Kanban command board
apps/debug_ui/streamlit_app.py         Streamlit AI-agent debug cockpit
```

### Manager-agent behavior

The agent should behave like a professional manager:

```text
Observe     - read ERP/WMS/MES/SiteTrack/market signals
Prioritize  - score severity, urgency, confidence, customer impact, inventory exposure, and partner KPI risk
Explain     - write a short business narrative for the case
Recommend   - propose mitigation options with tradeoffs
Escalate    - ask approval when policy requires it
Execute     - create governed writeback only after approval
Prove       - attach receipt, audit log, and optional blockchain proof anchor
Learn       - keep scenario/outcome data for future improvement
```

### What the agent must not do

```text
Do not bypass approval policy.
Do not write directly to ERP/WMS/TMS outside governed connectors.
Do not treat blockchain as a magic validator for bad source data.
Do not hide low-confidence recommendations.
Do not auto-close crisis cases without evidence.
```

---

## 2. News / market-signal mode: watches external risk signals

Run command:

```bash
cp .env.example .env
make demo-web
make demo-signals
```

Then inspect logs:

```bash
docker compose logs -f news_monitor
```

Optional RSS mode:

```bash
NEWS_MODE=rss NEWS_TOPIC=memory make demo-signals
```

Open:

```text
Kanban command board: http://localhost:8080
News API:             http://localhost:8000/news/items?topic=memory
News alerts:          http://localhost:8000/news/alerts?topic=memory
```

### Example use case: AI datacenter RAM lead-time risk

This mode is useful for market-driven risks such as:

```text
AI datacenter RAM lead-time volatility
HBM supply shortage
server DRAM price spike
NAND oversupply / inventory leakage
GPU supply bottleneck affecting server BOM
memory allocation changes from hyperscalers
```

The current `apps/news_monitor/` service can run in deterministic mode for demos or RSS mode for external monitoring. The allowlisted RSS config is in:

```text
apps/news_monitor/app/rss_sources.yaml
```

### Current news-monitor flow

```text
RSS / deterministic market signal
  -> apps/news_monitor/app/main.py
  -> POST /news/ingest
  -> news_items table
  -> news_alerts / risk-case enrichment
  -> Kanban command board / Streamlit debug cockpit
```

### Recommended signal extraction for AI datacenter RAM L/T

The agent should extract structured fields from each item:

```yaml
topic: memory
category: server_memory | dram | hbm | nand | gpu_related_memory
risk_type: lead_time | shortage | price_spike | allocation | inventory_leakage
market: spot | contract | hyperscaler | distributor | supplier
lead_time_delta_days: optional number
price_delta_pct: optional number
supplier: optional string
region: optional string
time_window: current | next_quarter | next_6_months
confidence: low | medium | high
```

Then map the signal to a Kanban case:

```text
Headline: AI datacenter RAM L/T volatility may affect Q3 server builds
Impact: open server orders, constrained RAM SKUs, customer commitments
Recommendation: check inventory, reserve allocation, hedge supplier split, escalate approval if premium buy is needed
Approval: required if cost impact or supplier change exceeds policy threshold
Evidence: source URL, timestamp, extracted fields, ERP impacted orders, optional blockchain proof anchor
```

---

## 3. Streamlit with AI agent

Run command:

```bash
pip install -r requirements-debug.txt
make debug-ui
```

Open:

```text
Streamlit debug cockpit: http://localhost:8501
```

Use Streamlit as the AI-agent cockpit for developers and operators who need to debug decisions.

Streamlit is best for:

```text
inspecting Kanban risk cases
viewing AI recommendation traces
checking policy / approval decisions
showing SiteTrack container evidence payloads
reviewing ERP/WMS/TMS writeback receipts
checking blockchain evidence-anchor status
replaying AI datacenter RAM lead-time scenarios
```

Streamlit should call FastAPI endpoints. It must not bypass the same policy, approval, audit, and connector paths used by the browser Kanban UI.

---

## 4. Browser Kanban UI vs Streamlit vs Grafana

```text
Browser Kanban UI  - main human workflow for supply-chain team lead / manager
Streamlit          - AI-agent debug cockpit and scenario inspection
Grafana            - later observability: latency, connector failure, ledger anchor success, freshness
```

Do not replace the Kanban operating model with Grafana. Grafana is for system health. The Kanban UI is for supply-chain operations.

---

## 5. Acceptance criteria

A good AI-agent demo should show:

```text
1. Manager-agent mode creates or updates a Kanban risk case from operating signals.
2. News mode can ingest or simulate an AI datacenter RAM lead-time signal.
3. The case explains impact, confidence, and recommended mitigation.
4. Approval policy is visible and cannot be bypassed.
5. Execution produces a receipt.
6. Audit evidence is visible.
7. Optional blockchain proof anchoring is treated as evidence, not as a substitute for source data quality.
```
