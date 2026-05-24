---
title: Supply Chain AI Agent
emoji: 🚚
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Supply Chain AI Agent

**Supply Chain AI Agent** is an ontology-driven operating layer for supply-chain teams. It co-works with traditional systems such as ERP, WMS, MES, TMS, supplier portals, CSV reports, market/news feeds, and optional blockchain evidence layers. The goal is not to replace existing systems; the goal is to connect them end-to-end, find major issues earlier, recommend actions, route approvals, execute governed writebacks, and keep proof for audit.

- GitHub: https://github.com/earlyBirdy/supply-chain-kanban
- Hugging Face demo: https://huggingface.co/spaces/earlyBirdy/supply-chain-kanban

`#SupplyChainAI` `#AIAgent` `#Ontology` `#Blockchain` `#ERP` `#WMS` `#MES` `#TMS` `#CommodityRisk` `#ROI`

## Concept in one loop

```text
Traditional systems + live news + supplier/logistics signals
  -> ontology objects
  -> AI risk detection
  -> major issue board
  -> recommendation + simulation
  -> human approval gate
  -> governed ERP/WMS/MES/TMS/supplier writeback
  -> receipt + audit + blockchain-ready proof
```

The simple UI is centered on one daily question for managers: **what are the major issues, what is the recommended action, who must approve it, and what proof will we keep after execution?**

## Ontology: from fragmented rows to supply-chain objects

Most supply-chain systems store the business as disconnected rows: ERP purchase orders, WMS stock movements, MES production records, TMS shipment events, supplier confirmations, quality holds, and finance reports. The agent maps these rows into common operating objects:

```text
Order
Shipment
Supplier
Material
InventoryPosition
ProductionOrder
QualityIssue
CustomerCommitment
RiskSignal
ActionReceipt
ApprovalDecision
```

This ontology layer lets the AI agent reason across systems. A delayed inbound material can be linked to inventory shortage, production risk, customer commitment exposure, supplier OTIF, cash impact, and the next approved recovery action.

## Co-working with traditional systems E2E

The product keeps existing systems as the source of operational truth, then adds an AI-agent decision layer above them:

```text
ERP    -> PO, SO, inventory, supplier, material master
WMS    -> stock, inbound, outbound, pick/pack status
MES    -> production order, yield, scrap, downtime, quality holds
TMS    -> shipment ETA, carrier delay, freight cost, route risk
Portal -> supplier confirmation, ASN, capacity, escalation
CSV    -> fast onboarding when APIs are not ready
```

Recommended integration mode is **read-only first**, then **approval-gated writeback**. This lowers implementation risk while still allowing the agent to create measurable operating value.

## Blockchain-ready evidence

Blockchain is treated as an evidence and trust layer, not as a magic database. The operational database stays fast for UI and workflow, while blockchain-style receipts can anchor:

```text
approval proof
supplier commitment proof
quality release proof
shipment checkpoint proof
ERP/WMS/TMS writeback receipt proof
audit and compliance evidence
```

This makes the supply-chain action trail easier to verify across teams, suppliers, customers, and auditors.

## Live news for commodity arrangement

The agent can track commodity and logistics news to help predict risk before it appears inside ERP. Examples include lithium/LFP battery materials, DRAM/NAND/HBM signals, copper price movement, port congestion, freight disruption, and supplier/geopolitical events.

```text
News signal -> commodity risk -> impacted material/order -> AI recommendation -> approval -> action receipt
```

This helps purchasing and planning teams adjust allocation, expedite timing, alternate sourcing, inventory buffers, and customer commitments earlier.

## CFO / ROI advantage

From a CFO view, the value is in reducing avoidable cost and operational risk while reusing existing systems:

```text
Lower expedite and premium freight cost
Lower inventory misallocation and shortage risk
Faster response to supplier and commodity shocks
Reduced revenue risk from missed customer commitments
Better approval control before external-system writebacks
Audit-ready evidence for finance, compliance, and customer review
Faster ROI because ERP/WMS/MES/TMS are integrated instead of replaced
```

The practical ROI story is simple: connect existing systems, detect the expensive exceptions earlier, approve the right action faster, and keep proof of every decision.

## AI agents + blockchain convergence

AI agents are the brain and hands: they sense supplier, shipment, inventory, quality, capacity, finance, and news signals; recommend recovery; prepare approvals; and execute governed writebacks. Blockchain-ready evidence is the judge and vault: it acts as a tamper-evident source of truth, and it anchors approval proof, supplier commitment proof, quality release proof, and external-system receipt proof. Together, they reduce trust friction while preserving human approval for high-impact actions.

## Simple AI leader dashboard

The main UI stays focused on one project-status page: summary KPIs, top major issues, E2E flow, AI Leader Dashboard, selected decision, and AI Agent Workbench. Semi-automated Sense -> Recommend -> Execute + Prove triage helps the user move from signal to action without hiding the approval gate.

## Power Templates

Power Templates show what the AI agent can do in realistic supply-chain situations:

```text
Commodity shock
Supplier OTIF rescue
Inventory rebalance
Quality hold recovery
Forecast vs capacity
Governed writeback
```

Each template links existing-system data, ontology objects, risk signals, recommended action, approval policy, execution receipt, and audit proof.


## Release notes

This repo now uses release notes instead of patch wording. Current release:

```text
Release: Supply Chain AI Agent — Ontology + Integration Demo
Status: professional repo structure, one-page project status UI, Hugging Face Docker demo, and Python quality gate
```

Highlights:

```text
- Product concept is centered on Supply Chain AI Agent.
- Ontology maps ERP/WMS/MES/TMS/supplier/news data into supply-chain objects.
- Traditional systems stay connected E2E through read-only import first and approval-gated writeback later.
- Blockchain-ready receipts preserve approval, supplier commitment, quality release, and writeback proof.
- Commodity and logistics news can become early risk signals for purchasing and inventory arrangement.
- CFO/ROI story focuses on reducing expedite cost, shortage risk, inventory misallocation, and audit friction.
- Hugging Face demo is documented for public sharing.
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


## Hugging Face demo

Public demo: https://huggingface.co/spaces/earlyBirdy/supply-chain-kanban

For a public hosted demo, use a Hugging Face **Docker Space**. The repo includes `Dockerfile.hf`, which runs the Supply Chain AI Agent API, seeded Postgres demo database, and static web UI in one container on port `7860`.

Quick local smoke test:

```bash
docker build -f Dockerfile.hf -t supply-chain-ai-agent-hf .
docker run --rm -p 7860:7860 supply-chain-ai-agent-hf
```

Then open `http://localhost:7860`. See `docs/demo/HUGGING_FACE_SPACE.md` for Space setup notes.
