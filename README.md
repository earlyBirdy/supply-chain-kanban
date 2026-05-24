# Supply Chain Kanban AI Agent

A professional supply-chain manager-agent that runs like a team lead or department manager: it watches daily operating signals, opens and updates Kanban risk cases, explains business impact, recommends mitigations, routes approvals, executes governed writebacks into existing systems, and keeps evidence for audit.

Kanban is the **regular supply-chain operations basis** for this repo. It is used every day for planning, purchasing, logistics, supplier follow-up, container tracking, approvals, and exception management. Crisis mode is a dashboard/view on top of the same Kanban model, not a separate product.

## Core design concept

This repo is different from a normal supply-chain dashboard, BI report, or ERP screen. It is designed as an **AI leader for the supply-chain team**. The agent should behave like a supply-chain team lead or department manager: it checks the operating situation, understands objects and constraints, opens the right Kanban cases, recommends actions, asks for approval when needed, executes typed writebacks, and keeps proof.

Most supply-chain systems see the world as tables:

```text
ERP rows
WMS rows
MES rows
TMS rows
BI rows
```

Leaders see the world as operational objects:

```text
orders
shipments
containers
plants
suppliers
customers
parts
BOM items
constrained resources
recovery actions
approval decisions
```

This repo is a minimal, runnable demonstration of a **Foundry-like pattern applied to supply chain**:

```text
Ontology / semantic layer
  Map fragmented facts into real-world objects and relationships.

Kinetic / execution layer
  Turn dashboards into actions through typed writebacks, approval gates, receipts, and audit trails.

Dynamic / evolution layer
  Evolve the model as new risks, rules, suppliers, products, and constraints appear without rewriting the whole stack.
```

In short: this is **not just dashboards**. It is an **operational supply-chain object graph** with AI-agent leadership, Kanban operations, governed execution, and blockchain-ready evidence.

## Blockchain for supply chain

Blockchain is used to strengthen supply-chain trust, transparency, and cross-party evidence. The default architecture keeps the application database as the fast operational store and uses blockchain as an evidence layer for:

```text
case lifecycle proof
approval proof
SiteTrack container checkpoint proof
ERP/WMS/TMS writeback receipt proof
supplier commitment proof
audit and compliance evidence
```

Advanced mode can use a permissioned blockchain as the append-only operational event ledger, while the application database becomes a read model for Kanban UI, API speed, analytics, and debugging. The key rule is that blockchain must not become a magic database. It still needs trusted external data layers from ERP, WMS, TMS, MES, SiteTrack, supplier portals, IoT, and verified APIs.

## Product loop

```text
ERP / WMS / TMS / SiteTrack / supplier / market signals
  -> canonical events
  -> risk case detection
  -> AI recommendation
  -> approval gate
  -> governed execution
  -> receipt + audit evidence
  -> Kanban command board
  -> supply-chain leader view: forecast / inventory / partner KPI / IOP alignment
```

The system should answer six management questions:

```text
What happened?
What is impacted?
What should we do?
Who must approve it?
What system changed?
Can we prove it later?
```

## Supply-chain leader view board

The primary operating surface should feel like a supply-chain team lead's daily control board, not only an exception list. It should help the leader ensure that forecasts, inventory, partners, and operating plans stay aligned.

The board should make these management jobs visible:

```text
Forecast accuracy and demand-change risk
Inventory alignment by part, plant, warehouse, and customer commitment
Supply gap / excess inventory / constrained-resource exposure
Partner performance: OTIF, yield, scrap, efficiency, responsiveness
Cross-functional planning actions with demand planning, finance, and operations
Approval blockers and governed execution receipts
```

The agent's role is to keep this view current, open Kanban cases when alignment breaks, recommend mitigation actions, and escalate only the cases that need management approval.

The simplified UI now separates the daily leader experience into four visible layers:

```text
AI Leader Dashboard
  Forecast alignment, inventory alignment, partner performance, and integrated operating-plan actions.

Project E2E Flow
  Supplier status -> IQC -> Assembly -> Test -> Packing -> OQC release.

Project Action Queue
  A simple risk-ranked list of cases, approvals, blockers, simulations, and receipts.

AI Agent Workbench
  Semi-automated Sense -> Recommend -> Execute + Prove triage with human approval preserved for governed writebacks.
```

This keeps the operator view simple: the agent watches many signals, but the user only sees the next management decision, the affected project stage, and the proof trail.


## AI agents + blockchain convergence

This project treats AI agents and blockchain as a collaborative operating pair for supply-chain management. AI agents are the **brain and hands**: they read fragmented ERP, WMS, MES, TMS, supplier, IoT, market, and logistics signals; predict disruption; recommend recovery; prepare approvals; and execute governed writebacks. Blockchain is the **judge and vault**: it gives the agent a tamper-evident source of truth for provenance, supplier commitments, quality release, settlement receipts, and audit proof.

The one-page Project E2E board now makes that convergence visible in the UI:

```text
Supplier signal
  -> IQC containment
  -> Assembly readiness
  -> Test recovery
  -> Packing / logistics cutoff
  -> OQC release
  -> receipt + blockchain-ready proof
```

High-impact scenarios this demo is designed to communicate:

```text
Autonomous procurement and settlement
Real-time traceability and cold-chain accountability
Continuous risk simulation and mitigation
Machine-to-machine microtransactions for logistics, handling, tolling, charging, and recovery
Reduced trust friction through immutable evidence
Lower latency by removing routine human bottlenecks while preserving approval gates
Always-on resilience when supplier, shipment, quality, or capacity shocks appear
```

## How the AI agent works now

The repo has two AI-agent paths. Both feed the same Kanban command board.

### Path 1 — supply-chain team lead / department manager

```bash
cp .env.example .env
make demo-agent
```

Open:

```text
Kanban command board: http://localhost:8080
API docs:              http://localhost:8000/docs
```

Flow:

```text
ERP / WMS / MES / SiteTrack signals
  -> risk scoring
  -> Kanban risk case
  -> impact analysis
  -> AI recommendation
  -> approval gate
  -> governed writeback
  -> receipt + audit evidence
```

Use this when the product should behave like a supply-chain team lead: watch the board, prioritize risk, explain impact, recommend action, escalate approvals, and prove what changed.

### Path 2 — news / market-signal monitor

```bash
cp .env.example .env
make demo-web
make demo-signals
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

Example: AI datacenter RAM lead-time volatility can become a memory supply-risk signal, then a Kanban risk case with impacted orders, recommended supplier/inventory action, approval policy, execution receipt, and audit evidence.

Detailed doc: `docs/product/AI_AGENT_OPERATING_MODEL.md`.


## Release notes

This repo now uses release notes instead of patch wording. Current release:

```text
Release: Supply Chain Kanban AI Agent — Operations Basis
Status: professional repo structure, Python-only quality gate, Kanban regular-operations model
```

Highlights:

```text
- Kanban is defined as the daily supply-chain operations basis.
- Crisis operations is a dashboard/view over the same Kanban cases.
- Devpost and Gemini-specific demo content are removed from the professional core.
- BI is retained as an optional analytics/reporting layer for later ERP-adjacent use.
- Running commands are documented in README and docs/demo/RUN_LOCAL_UI.md.
```

Detailed release file: `RELEASE_NOTES.md`.

## Clean repo tree

```text
apps/
  api/                         FastAPI runtime, risk cases, actions, approvals, connectors
  web/                         human Kanban command board
  news_monitor/                optional market-signal adapter
  manager_agent_blueprints/    manager-agent behavior and role blueprints
contracts/                     canonical contracts: actions, lifecycle, ontology, control-plane manifest
data/
  seed_sql/                    local demo schema/views/seed packs
  sample_inputs/               sample CSV inputs
  ingest_samples/              ERP/WMS/MES sample payloads
  analytics_sql/               optional SQL models
operations/
  dashboards/                  Kanban/crisis dashboard definitions
  governance/                  policy, cadence, auto-execution rules
  planning/                    constrained-resource and decision-scoring examples
  scenarios/                   crisis scenario packs
  ui_views/                    dashboard/layout specs
integrations/
  alerting/                    Slack/alert integration templates
  market_signals/              market signal adapters and config
  supplier_portal/             supplier portal spec
infra/                         deployment notes and cloud scaffolding
docs/
  architecture/                architecture and evidence-ledger docs
  product/                     product scope, Kanban model, agent behavior
  integrations/                ERP/SSO/SiteTrack integration notes
  operations/                  data, governance, JSON contracts, removal plan
  compliance/                  optional compliance references
  business/                    ROI and business model notes
  demo/                        demo script and local demo notes
  assets/                      diagrams and images
tests/                         API, policy, approval, audit, connector tests
```

## Core architecture docs

Start here:

- `docs/architecture/ARCHITECTURE.md`
- `docs/product/KANBAN_OPERATING_MODEL.md`
- `docs/product/AI_AGENT_OPERATING_MODEL.md`
- `docs/architecture/BLOCKCHAIN_SITETRACK_ERP_STRATEGY.md`
- `docs/architecture/BLOCKCHAIN_OPERATIONAL_DATABASE_DECISION.md`
- `docs/architecture/CANONICAL_CONTROL_PLANE.md`
- `docs/operations/GOVERNANCE.md`
- `docs/demo/RUN_LOCAL_UI.md`
- `docs/product/UI_FRAMEWORK_DECISION.md`
- `docs/product/DEBUG_UI_DECISION.md`

## What is core

```text
apps/api/app/api/routers/operator.py          Kanban command-board API
apps/api/app/api/routers/cases.py             risk case API
apps/api/app/api/routers/actions.py           governed action API
apps/api/app/api/routers/pending_actions.py   approval queue API
apps/api/app/api/routers/governance.py        policy/governance API
apps/api/app/audit.py                         audit and request-id evidence
apps/api/app/rbac.py                          role checks
apps/api/app/approval.py                      approval policy resolution
apps/api/app/idempotency.py                   safe execution dedupe
apps/api/app/connectors/                      ERP/WMS/TMS/supplier connector stubs
contracts/                                    action/lifecycle/ontology contracts
operations/governance/policy.yaml             runtime policy
apps/web/public/                              professional Kanban UI
```

## What was removed from the core

The repo no longer includes Devpost submission copy or model-specific Gemini live scaffolding. BI is **kept for further usage** as an optional integration/analytics layer, similar to ERP/WMS/TMS integrations. BI must stay outside the default operational path, but dashboard specs and analytics SQL are kept for future reporting, executive review, and ERP-adjacent analytics.

## Run locally and open the Kanban dashboard

### Recommended browser demo

```bash
cp .env.example .env
make demo-web
```

Open in your browser:

```text
Kanban command board: http://localhost:8080
API docs:              http://localhost:8000/docs
Health check:          http://localhost:8000/healthz
Readiness check:       http://localhost:8000/readyz
```

### API-only mode

```bash
cp .env.example .env
make demo-min
```

Open:

```text
API docs: http://localhost:8000/docs
```

### Manager-agent mode

```bash
cp .env.example .env
make demo-agent
```

Open:

```text
Kanban command board: http://localhost:8080
API docs:              http://localhost:8000/docs
```

Use this when you want the repo to behave more like a supply-chain team lead: the background agent polls signals, updates cases, and creates/recommends governed actions.

### Stop or reset

```bash
make down     # stop containers, keep DB volume
make reset    # stop containers and remove DB volume
make logs     # tail API/agent/signal logs
make status   # docker status + smoke checks
```

Detailed runbook: `docs/demo/RUN_LOCAL_UI.md`.
UI framework decision: `docs/product/UI_FRAMEWORK_DECISION.md`.

### Docker demo troubleshooting

If Docker is not running, `make demo-web` or `make demo-agent` fails before the repo starts:

```text
Cannot connect to the Docker daemon
```

Start Docker Desktop first, then rerun the same command.

If `db_init` fails, inspect the init logs first:

```bash
docker compose logs db_init
```

The demo database is initialized by `data/seed_sql/00_schema.sql`, `01_seed_demo.sql`, and `02_views.sql`. The schema must create referenced tables before any foreign-key references; `make test` includes a guard for that ordering.

## Streamlit AI-agent debug cockpit

Use Streamlit for internal AI-agent debugging, not as the final operator UI.

```bash
pip install -r requirements-debug.txt
make debug-ui
```

Open:

```text
Streamlit debug cockpit: http://localhost:8501
```

The Streamlit cockpit reads FastAPI endpoints and is designed for case inspection, recommendation traces, SiteTrack evidence payloads, ERP writeback receipts, and blockchain proof status.


## Quality gate

```bash
make test
# runs: python3 scripts/run_checks.py
```

The local gate uses Python syntax compilation plus pytest so it can run in constrained sandboxes.

## Design principle

Keep the product simple and professional:

```text
Signal -> Kanban case -> Recommendation -> Approval -> Execution -> Receipt -> Audit
```

Every feature must make that loop faster, safer, or easier for a supply-chain manager to explain.
