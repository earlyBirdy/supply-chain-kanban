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
- Hugging Face demo: coming soon...

`#SupplyChainAI` `#AIAgent` `#Ontology` `#Blockchain` `#ERP` `#WMS` `#MES` `#TMS` `#CommodityRisk` `#ROI`

## Concept in one loop

```text
ingest system data from ERP/MES/WMS/TMS/supplier/news/blockchain evidence
  -> map to ontology
  -> detect risks
  -> predict disruptions
  -> recommend actions
  -> require human approval
  -> create writeback receipt
  -> audit trail + decision hashes + tamper-resistant evidence
```



## Dashboard ontology enhancement: ERP/MES + AI agent + blockchain proof + simple UX

This patch strengthens the dashboard ontology so it can behave like a practical supply-chain control room instead of a raw data-board. The new structure adds source-system references, BOM exposure, MES capacity constraints, S&OP exceptions, AI-agent run traces, governed writeback receipts, and persona-specific simple UI contracts.

```text
ERP / MES / WMS / TMS / Supplier Portal / CSV / News / Blockchain Evidence
  -> SourceSystemConnector + SourceRecordReference
  -> Order / InventoryPosition / ProductionRecord / BillOfMaterialsExposure / CapacityConstraint
  -> NewsRiskSignal + CommodityPredictionPacket
  -> AgentRun + AgentDecision + PendingAction
  -> human approval
  -> WritebackReceipt + EvidenceReceipt + optional BlockchainAnchor
  -> SimpleUIView for planner / CFO / plant / supplier manager
```

Key design rules:

- **ERP/MES compatibility:** every prediction and dashboard object keeps source-system keys, table names, record IDs, confidence, validation status, and writeback target.
- **AI-agent automation:** the agent may read, map, score, predict, simulate, and recommend automatically; ERP/MES/WMS/TMS writeback still requires visible human approval.
- **Blockchain datasets:** blockchain is an audit/proof layer for receipt hashes, decision hashes, source-record hashes, and action receipt IDs; it is not the default operational database.
- **News prediction:** news and market data become ontology-linked risk packets with 人事時地物, source confidence, time period, price ranges, BOM exposure, supplier exposure, and follow-up triggers.
- **Simple UI view:** the first screen answers one manager question: what are the top issues, what action is recommended, who approves, which system changes, and what proof is kept?

Updated references:

- `contracts/supply_chain_ontology.yaml` / `.json`
- `apps/api/app/ontology.yaml` / `.json`
- `docs/product/ONTOLOGY_INTEGRATION_BLUEPRINT.md`
- `docs/operations/DATASETS.md`
- `data/sample_inputs/dashboard_ontology_sample.json`

## Agent skills + autoresearch extension

The uploaded `skills-main` and `autoresearch` references were folded into the product direction as operating patterns, not as runtime dependencies. They guide agent behavior through product/design patterns without adding heavy runtime dependencies. The repo now treats the AI agent as a disciplined supply-chain teammate:

```text
Skill playbook      -> clarify business change, triage issues, produce PRD/issue slices
Autoresearch loop   -> run bounded experiments against forecast/risk hypotheses
Dashboard ontology  -> expose the result as ForecastPlan, InventoryPosition, NewsRiskSignal, AgentDecision, and EvidenceReceipt
Human approval gate -> keep ERP/MES/WMS/TMS writebacks governed
```

This means the demo can show more than a dashboard: it can explain **how the agent decides**, **how an operator reviews the recommendation**, **how a bounded experiment improves risk prediction**, and **how the final action stays auditable**.

See `docs/product/AGENT_SKILLS_AND_AUTORESEARCH_PLAYBOOK.md` for the implementation playbook.

The simple UI is centered on one daily question for managers: **what are the major issues, what is the recommended action, who must approve it, what system will change, and what proof will we keep after execution?**

## Ontology-first positioning: from fragmented rows to supply-chain objects

Most supply-chain systems store the business as disconnected rows: ERP purchase orders, WMS stock movements, MES production records, TMS shipment events, supplier confirmations, quality holds, and finance reports. The repo models real-world supply-chain objects instead of only showing ERP/MES/WMS rows. The agent maps these rows into common operating objects:

```text
Order
Shipment
Supplier
Plant
Material
ForecastPlan
InventoryPosition
ProductionOrder
QualityIssue
CustomerCommitment
PartnerPerformanceMetric
NewsRiskSignal
AgentDecision
EvidenceReceipt
```

This ontology-first layer lets the AI agent reason across systems. A delayed inbound material can be linked to inventory shortage, MES build risk, customer commitment exposure, supplier OTIF, plant capacity, cash impact, news-driven commodity risk, and the next approved recovery action. The contract includes orders, suppliers, plants, forecasts, inventory positions, partner metrics, news risks, and agent decisions so the UI can explain the business decision instead of only showing raw system rows.

## ERP / MES / WMS / TMS integration story

Traditional ERP/MES/WMS/TMS systems feed into the ontology layer as source systems, not the final user experience. The product keeps existing systems as the source of operational truth, then adds an AI-agent decision layer above them:

```text
ERP    -> PO, SO, inventory, supplier, material master
WMS    -> stock, inbound, outbound, pick/pack status
MES    -> production order, yield, scrap, downtime, quality holds
TMS    -> shipment ETA, carrier delay, freight cost, route risk
Portal -> supplier confirmation, ASN, capacity, escalation
CSV    -> fast onboarding when APIs are not ready
```

Recommended integration mode is **read-only first**, then **approval-gated writeback**. This lowers implementation risk while still allowing the agent to create measurable operating value without forcing users to live inside ERP/MES/WMS/TMS screens.

## Blockchain-ready evidence

Blockchain is treated as an audit, evidence, and trust layer, not a required default runtime dependency and not a magic database. The operational database stays fast for UI and workflow, while blockchain-style receipts can anchor traceable receipts, decision hashes, and tamper-resistant evidence:

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

The agent can track news/risk signals as inputs for commodity, supplier, logistics, and geopolitical risk prediction before the risk appears inside ERP. Examples include lithium/LFP battery materials, DRAM/NAND/HBM signals, copper price movement, port congestion, freight disruption, and supplier/geopolitical events.

News is not shown as headlines. News is converted into ontology-linked risk signals. The AI agent maps each event to affected commodities, suppliers, logistics lanes, financial exposure, and recommended approval-gated actions.

News is converted into ontology-linked commodity risk signals. The AI agent maps each event to affected materials, BOM exposure, suppliers, industries, price risk, lead-time risk, and approval-gated actions.

Every news, market, supplier, price, and BOM signal must be stored with ERP/MES-compatible metadata. The AI agent does not only say “shortage risk.” It explains 人事時地物: who is affected, what changed, when the trend formed, where the risk appears, which materials/products are exposed, what source supports the signal, what confidence level it has, what price range changed, and what approval-gated action should happen next.

A predictive agent answer should look like this, not like a headline summary:

```text
For the last 6 months, memory showed rising AI demand, supplier capacity shift, price momentum, stock/ETF confirmation, and BOM exposure. The news headline confirms a trend already detected earlier.

People / orgs: memory suppliers, ERP vendor IDs, affected customers, approval owners
Event: AI demand rose, capacity shifted, prices moved, lead times changed
Time: last 6 months lookback + next 6-12 months prediction window
Place: supplier region, plant, warehouse, logistics lane, customer market
Object: DRAM, NAND, HBM, DDR5, SSD, BOM component, SKU, order, work order
Sources: news, market report, supplier quote, ERP PO, MES demand, WMS inventory, stock/ETF signal
Confidence: source confidence %, combined model confidence %, evidence quality score
Price range: contract/spot/quote range, change %, currency, valid-from/valid-to period
Action: supplier review, LTA, buffer, alternate source, procurement hold, margin scenario
```

For real ERP/MES interconnection, this short explanation must be backed by a full `commodity_prediction_packet.v1` evidence packet with `prediction_id`, `schema_version`, `human_context` for 人事時地物, `erp_mes_wms_tms_mapping`, detailed `price_ranges`, `sources` with `source_confidence`, `extraction_confidence`, `model_confidence`, approval owner, writeback targets, evidence hash, decision hash, and action receipt. The primary planner-facing layer should use a **Supply Chain Risk Review / S&OP Exception Report** because supply-chain teams decide signal, risk, exposure, business impact, scenarios, options, recommendation, owner, evidence confidence, and follow-up triggers. **5 Why + 8D-lite** remains as a supporting RCA/corrective-action appendix for root cause, containment, validation, recurrence prevention, and evidence closure. See `docs/product/COMMODITY_TREND_RADAR.md` for the complete memory packet example.

```text
News signal -> ontology-linked risk signal -> commodity/BOM/supplier/logistics/finance impact -> AI recommendation -> approval-gated action -> action receipt
```

This helps purchasing and planning teams adjust allocation, expedite timing, alternate sourcing, inventory buffers, and customer commitments earlier.


## IT / Defense Commodity Trend Radar

The repo now includes an early-warning radar for likely IT and defense commodity shortages in the coming 6-12 months. The agent does not wait for mainstream shortage news. It watches weak signals from demand acceleration, supply tightness, price momentum, export-control stress, BOM exposure, supplier lead-time changes, and news confirmation.

Current watchlist:

```text
Memory chips: HBM, DDR5/DRAM, NAND/SSD
Advanced packaging: ABF substrate, CoWoS capacity, silicon interposers
Critical semiconductor minerals: gallium, germanium, indium, tantalum
Rare earth magnets: NdPr, dysprosium, terbium, yttrium
Defense metals: tungsten and antimony
High-reliability passives: MLCC, tantalum capacitors, resistors
```

The API exposes this as an evidence-ready trend radar:

```bash
curl http://localhost:8000/commodity_trends/
```

See `docs/product/COMMODITY_TREND_RADAR.md` and `data/sample_inputs/commodity_trend_radar_it_defense.json`.

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
- `docs/product/ONTOLOGY_INTEGRATION_BLUEPRINT.md`
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



## Dashboard ontology enhancement

The dashboard now includes an ontology enhancement path for ERP/MES + AI agent + blockchain proof + simple UX/UI:

- **ERP/MES/WMS/TMS source mapping**: source records stay traceable through `SourceSystemConnector` and `SourceRecordReference` instead of becoming raw dashboard tables.
- **Agent skills + autoresearch extension**: `/agent_skills/` exposes skills for clarify → map → convert news to risk → build decision packet → governed handoff, plus bounded research sprints for prediction improvement.
- **Live news for commodity arrangements**: `/news/items` and `/news/check-now?topic=commodities` convert commodity headlines into risk signals with source confidence, time period, price range, BOM exposure, and recommended arrangements.
- **Commodity Trend Radar**: `/commodity_trends/` ranks IT/Defense commodities with early-warning score, source confidence, price range, BOM exposure, approval gate, and proof hash.
- **Blockchain-ready proof**: decisions keep `EvidenceReceipt`, `WritebackReceipt`, `BlockchainAnchor`, evidence hash, and decision hash as proof; blockchain is an evidence layer, not the operational database.
- **Simple UX rule**: default view shows the top issue, affected object, recommended action, approval owner, target system, and proof. Raw ERP/MES records remain available through source references.

See `docs/product/DASHBOARD_ONTOLOGY_ENHANCEMENT.md` for the implementation map.

## Hugging Face demo

Public demo: https://huggingface.co/spaces/earlyBirdy/supply-chain-kanban

For a public hosted demo, use a Hugging Face **Docker Space**. The repo includes `Dockerfile.hf`, which runs the Supply Chain AI Agent API, seeded Postgres demo database, and static web UI in one container on port `7860`.

Quick local smoke test:

```bash
docker build -f Dockerfile.hf -t supply-chain-ai-agent-hf .
docker run --rm -p 7860:7860 supply-chain-ai-agent-hf
```

Then open `http://localhost:7860`. See `docs/demo/HUGGING_FACE_SPACE.md` for Space setup notes.

## XPRIZE / Devpost real-business submission mode

This repo now includes a real-business submission path for Devpost/XPRIZE review. It is designed to show more than a static dashboard:

1. **Continuous AI agent** — reads ERP/MES/WMS mock data plus news/risk signals, detects inventory, supplier, and production risk, and creates recommended actions.
2. **Human approval gate** — a Planner, CFO, or Operations manager approves, rejects, or requests more evidence before any simulated ERP/MES/WMS writeback.
3. **Evidence log** — every agent decision includes source inputs, confidence, a decision hash, receipt hash, blockchain-ready proof status, and Gemini/API trace fields.
4. **Revenue/customer evidence** — the demo includes a pilot offer and proof checklist for a pilot user, signed LOI, Stripe invoice, or paid consulting/demo package.

Business-readiness API:

```bash
curl http://localhost:8000/business_submission/
curl -X POST http://localhost:8000/business_submission/run
```

The safe default remains read-only monitoring. External-system writeback is simulated and approval-gated for the demo.


## Commodity Arrangement Desk

The dashboard now converts live news and Commodity Trend Radar signals into approval-ready commodity arrangement cards. Instead of showing raw headlines first, the UI shows commodity/material, source confidence, time period, price range, BOM exposure, ERP/MES fields to check, recommended arrangement, approval owner, governed writeback target, and evidence hash.

```bash
curl http://localhost:8000/news/commodity-arrangements?topic=commodities
```

This keeps live commodity research useful for planners: buy timing, buffer/safety stock, LTA, alternate supplier/substitution, expedite, and allocation decisions stay human-approved and proof-backed.
