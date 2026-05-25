# Ontology + ERP/MES AI Agent Blueprint

This repo demonstrates a supply-chain AI leader layer that sits above existing ERP, MES, WMS, TMS, supplier, news, and evidence systems. The design goal is simple: keep traditional systems as the source of operational truth, then use an ontology and governed AI-agent workflow to detect major issues earlier, recommend action, route approval, execute writebacks, and preserve proof.

## Operating loop

```text
ERP/MES/WMS/TMS/Supplier/CSV/News
  -> canonical ontology objects
  -> AI prediction and decision packet
  -> simple major-issue dashboard
  -> human approval gate
  -> governed writeback
  -> evidence receipt + blockchain-ready anchor
```

## Ontology structure

The ontology is organized around objects that business leaders already use:

```text
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

This gives the agent one shared language for ERP orders, MES production quality, WMS stock, TMS shipment risk, supplier promises, and market/news disruption.

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

The AI agent can automate sensing, mapping, ranking, simulation, recommendation, and draft actions. It must not silently change ERP/MES/WMS/TMS records. External-system writes require:

1. a visible `AgentDecision`,
2. business-impact explanation,
3. evidence references,
4. policy/approval state,
5. execution receipt,
6. audit and blockchain-ready proof.

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

