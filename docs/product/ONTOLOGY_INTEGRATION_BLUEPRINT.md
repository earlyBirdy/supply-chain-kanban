# Ontology + ERP/MES AI Agent Blueprint

This repo demonstrates a supply-chain AI leader layer that sits above existing ERP, MES, WMS, TMS, supplier, news, and evidence systems. The design goal is simple: keep traditional systems as source systems feeding the ontology layer, not as the final user experience; then use a governed AI-agent workflow to detect major issues earlier, recommend action, route approval, execute writebacks, and preserve proof.

## Operating loop

```text
ingest system data from ERP/MES/WMS/TMS/Supplier/CSV/News
  -> map to ontology
  -> detect risks
  -> predict disruptions
  -> recommend actions
  -> require human approval
  -> create writeback receipt
  -> evidence receipt + blockchain-ready anchor
  -> decision hashes + tamper-resistant evidence
```

## Ontology structure

The ontology-first structure models real-world supply-chain objects instead of only showing ERP/MES/WMS rows. It is organized around objects that business leaders already use:

```text
Order                     customer/order promise, service exposure, source-system refs
Supplier                  partner identity, commitment, escalation path
Plant                     factory/site capacity, constraint, production context
ForecastPlan              demand forecast, customer commitment, confidence, revenue exposure
InventoryPosition         stock, allocation, projected shortage, projected excess
PartnerPerformanceMetric  OTIF, yield, scrap, efficiency, response aging, PPM
NewsRiskSignal            commodity/logistics/supplier/geopolitical news risk
Case                      active AI risk case
KanbanCard                simple UI card for the human operator
AgentDecision             recommendation, business impact, approval state, evidence refs
EvidenceReceipt           validated proof attached to the decision/action
BlockchainAnchor          tamper-evident hash anchor for the receipt
```

This gives the agent one shared language for orders, suppliers, plants, forecasts, inventory positions, partner metrics, news risks, and agent decisions across ERP orders, MES production quality, WMS stock, TMS shipment risk, supplier promises, and market/news disruption.

For NEWS features, news is not shown as headlines. News is converted into ontology-linked risk signals. The AI agent maps each event to affected commodities, suppliers, logistics lanes, financial exposure, and recommended approval-gated actions. News is converted into ontology-linked commodity risk signals, then mapped to affected materials, BOM exposure, suppliers, industries, price risk, lead-time risk, and approval-gated actions.

Every news, market, supplier, price, and BOM signal must be stored with ERP/MES-compatible metadata. The AI agent does not only say “shortage risk.” It explains 人事時地物: who is affected, what changed, when the trend formed, where the risk appears, which materials/products are exposed, what source supports the signal, what confidence level it has, what price range changed, and what approval-gated action should happen next.

A proper shortage prediction should include source confidence %, extraction confidence %, model confidence %, time period, price range, ERP/MES/WMS/TMS references, and evidence receipts. For example: “For the last 6 months, memory showed rising AI demand, supplier capacity shift, price momentum, stock/ETF confirmation, and BOM exposure. The news headline confirms a trend already detected earlier.” This sentence is only the planner-facing summary. For business users, the primary planner view should be a **Supply Chain Risk Review / S&OP Exception Report** covering signal, risk, exposure, business impact, scenario planning, options, recommendation, owner/approval, evidence confidence, and follow-up triggers. 5 Why and 8D-lite remain as a supporting RCA/corrective-action appendix, not the main supply-chain view. The machine-readable output must use the full `commodity_prediction_packet.v1` structure with `human_context` for 人事時地物, ERP vendor/material IDs, PO/WO/lot references, plant/warehouse/lane references, price min/max ranges, publish dates, confidence percentages, approval owner, writeback target, evidence hash, decision hash, and action receipt.

## Integration pattern

Use **read-only first** integrations until the board proves value. After that, enable **approval-gated writeback** only for well-defined actions.

| System | Read signals | Writeback after approval |
| --- | --- | --- |
| ERP | PO, SO, inventory, supplier/material master, cost exposure | purchase request, PO update, allocation note |
| MES | production order, yield, scrap, downtime, IQC/OQC hold | quality disposition request, build-priority note |
| WMS | inbound/outbound movement, pick/pack status, warehouse exception | allocation move, expedite pick/pack task |
| TMS | ETA, route risk, carrier delay, freight cost | expedite/reroute request |
| Supplier Portal | confirmation, ASN, OTIF, capacity promise | supplier escalation ticket |
| News Monitor | commodity, logistics, supplier, geopolitical signal | no writeback; creates risk signal only |
| Blockchain Evidence | receipt hash, approval proof, supplier commitment proof | anchor receipt hash only; not operational truth |

## AI-agent automation boundary

The AI agent can automate the explicit loop: ingest system data, map to ontology, detect risks, predict disruptions, recommend actions, require human approval, and create writeback receipt. It must not silently change ERP/MES/WMS/TMS records. External-system writes require:

1. a visible `AgentDecision`,
2. business-impact explanation,
3. evidence references,
4. policy/approval state,
5. execution receipt,
6. audit and blockchain-ready proof with traceable receipts, decision hashes, and tamper-resistant evidence.

## Simple UI view

The dashboard should avoid raw table overload. The first screen should answer:

```text
What are the top major issues?
Which forecast/inventory/partner KPI is driving the risk?
What action is recommended?
Who must approve it?
What system will be changed?
What proof will we keep?
```

The UI now separates:

- **Project status**: major issues, E2E flow, leader KPI cards, next decision.
- **Integrations**: ERP/MES/WMS/TMS/supplier/news/blockchain connection map.
- **Ontology Decision Map**: the objects used by the AI agent.
- **Templates + news**: commodity shock, supplier OTIF, inventory rebalance, forecast/capacity, and governed writeback demos.

## CFO / ROI view

The CFO-facing value is not “more dashboards.” It is earlier exception detection and controlled execution:

```text
lower expedite and premium freight cost
lower shortage and excess-inventory risk
lower missed-commitment revenue risk
faster supplier/quality escalation
better approval control before system writebacks
audit-ready proof for finance, customer, and compliance review
```


## Dashboard ontology enhancement

The improved structure adds a practical bridge between the dashboard and real ERP/MES environments. The dashboard should not ask users to understand every raw table. It should preserve the raw source reference in the background, then show the business object in front.

### 1. Source-system connector layer

Each inbound system is represented by `SourceSystemConnector` and every normalized row keeps a `SourceRecordReference`.

```text
ERP/MES/WMS/TMS/Portal/News/CSV/Blockchain
  -> SourceSystemConnector
  -> SourceRecordReference
  -> ontology object
  -> AI Agent decision
  -> approval-gated writeback receipt
```

This is the key to interconnection with current ERP/MES systems. It keeps the original vendor/table/record/version/source confidence/extraction confidence fields so a planner can trace a risk card back to the real PO, WO, inventory row, shipment event, news signal, or evidence receipt.

### 2. Supply-chain operating objects

The ontology enhancement adds four objects that make the dashboard more useful for supply-chain people:

| Object | Why it matters |
| --- | --- |
| `BillOfMaterialsExposure` | Links commodity/news risk to affected SKUs, ERP material IDs, POs, WOs, plants, suppliers, and revenue exposure. |
| `CapacityConstraint` | Converts MES yield, downtime, line capacity, quality hold, manpower, tooling, or material shortage into a supply constraint. |
| `SAndOPException` | Gives planners a natural exception report: signal, impact, scenarios, recommended option, owner, approval, and follow-up triggers. |
| `SimpleUIView` | Defines what each persona should see first so the UI stays simple instead of becoming a raw-table dashboard. |

### 3. AI-agent automation boundary

The AI agent is allowed to read, normalize, score, simulate, recommend, and draft writeback payloads automatically. It must request approval before external writeback. This makes the automation useful without making ERP/MES governance unsafe.

```text
Allowed automatically:
read -> map -> score -> predict -> simulate -> recommend -> prepare receipt

Requires human approval:
ERP/MES/WMS/TMS/SupplierPortal writeback, purchase commitment, allocation change, customer-impacting action

Blocked:
silent source-system changes, untraceable model-only decisions, writeback without receipt
```

### 4. Blockchain dataset model

Blockchain remains a proof layer. The operational truth stays in the application database and existing systems. The anchored dataset is small and audit-oriented:

```text
EvidenceReceipt
WritebackReceipt
AgentDecision
TraceabilityEvent
receipt_hash / decision_hash / source_record_hashes / action_receipt_id
```

This keeps the UI fast and ERP/MES-compatible while still giving customers tamper-evident proof when they need supplier, finance, customer, or compliance evidence.

### 5. Simple UI and user experience

The default user experience should be a control-room page, not a complicated data model explorer.

```text
Home question:
What are the top major issues, what action is recommended, who must approve,
which system changes, and what proof is kept?
```

Recommended information hierarchy:

1. Top major issues only.
2. AI Leader Dashboard: forecast, inventory, partner KPI, and IOP actions.
3. Project E2E flow: supplier status -> IQC -> assembly -> test -> packing -> OQC.
4. Next decision: affected object, impact, recommendation, approval owner.
5. Simulate + execute: show before/after impact and target system.
6. Prove: writeback receipt, evidence receipt, decision hash, blockchain anchor status.
7. Audit timeline: who approved what, when, why, and from which source data.

This is why `SimpleUIView` is now a first-class ontology object. It lets product, engineering, and demo scripts describe the user experience with the same ontology that the agent uses for reasoning.
