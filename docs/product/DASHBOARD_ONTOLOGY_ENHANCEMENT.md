# Dashboard Ontology Enhancement

This enhancement keeps the product simple for supply-chain users while extending the ontology and dashboard around four enterprise needs:

1. **ERP/MES interconnection** — source records from ERP, MES, WMS, TMS, supplier portal, CSV, and news are mapped into canonical objects instead of shown as raw tables.
2. **AI agent skills** — the agent has small, auditable skills for clarifying operator asks, mapping source records, converting news into commodity risk, building decision packets, and handing off governed work.
3. **Blockchain-ready proof** — decisions keep `EvidenceReceipt`, `WritebackReceipt`, `BlockchainAnchor`, source confidence, decision hash, and evidence hash attached to the case.
4. **Simple UX/UI** — the default dashboard answers: top issue, affected object, recommended action, approval owner, writeback target, and proof.

## Updated operating loop

```text
ERP/MES/WMS/TMS/supplier/news signal
  -> SourceSystemConnector + SourceRecordReference
  -> canonical ontology object
  -> AgentSkill triage
  -> Commodity Trend Radar or risk model
  -> AgentDecision packet
  -> human approval
  -> governed writeback
  -> EvidenceReceipt / BlockchainAnchor proof
  -> simple manager card
```

## New runtime surfaces

| Surface | Purpose |
| --- | --- |
| `/agent_skills/` | Returns the agent skill catalog and autoresearch extensions used by the UI. |
| `/commodity_trends/` | Returns IT/Defense Commodity Trend Radar with source confidence, price range, BOM exposure, and proof hash. |
| `/news/items` | Shows news converted into ontology-linked risk signals. |
| `/news/check-now?topic=commodities` | Inserts deterministic commodity demo signals in dev mode. |

## Ontology additions

| Object | Why it exists |
| --- | --- |
| `AgentSkill` | Makes agent capability explicit and auditable instead of vague “AI magic.” |
| `AutoresearchExperiment` | Lets the product test forecast/news/supplier model improvements with promotion gates. |
| `SimpleUXDecisionCard` | Preserves a simple operator view while linking to deeper ERP/MES/source/proof records. |

## Commodity arrangement logic

The Commodity Trend Radar is not a headline feed. It converts weak signals into practical arrangements:

- buy timing review;
- buffer / safety stock;
- long-term agreement or allocation reservation;
- alternate supplier or substitution review;
- customer allocation or quote-renewal review.

Each radar row now carries:

- time period;
- source confidence;
- price range;
- BOM exposure summary;
- approval gate;
- evidence hash.

## UX rule

The dashboard should not ask a planner to read ERP/MES tables first. The first screen should show the manager-ready decision:

```text
What changed?
Which material / supplier / plant / order is affected?
What is the service, cost, and risk impact?
What action does the AI recommend?
Who must approve?
Which system will be updated?
What receipt/proof will be attached?
```
