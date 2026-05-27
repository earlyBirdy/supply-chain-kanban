# Agent Skills and Autoresearch Playbook

This playbook adapts the uploaded `skills-main` and `autoresearch` repositories into the Supply Chain AI Agent product direction. They are used as product/design patterns that guide agent behavior, not as required runtime dependencies or heavy dependencies added to the default app.

## Why this matters

A supply-chain dashboard becomes valuable when it can repeatedly turn noisy signals into governed action. The agent therefore needs two disciplines:

1. **Agent skills** — a repeatable way to clarify ambiguous operator requests, create PRD-quality issue slices, triage work, and hand off decisions.
2. **Autoresearch loop** — a bounded experiment process for improving forecast, inventory, supplier, and news-risk models without changing the production agent blindly.

## Operating loop

```text
Business ask or live signal
  -> ingest system data
  -> skill-driven clarification
  -> map to ontology
  -> detect risks
  -> bounded risk/forecast experiment when needed
  -> predict disruptions
  -> recommend actions through AI AgentDecision
  -> require human approval
  -> ERP/MES/WMS/TMS/supplier writeback
  -> create writeback receipt
  -> EvidenceReceipt / blockchain-ready proof
  -> decision hashes + tamper-resistant evidence
```

## Skill layer for supply-chain work

| Skill pattern | Supply-chain use |
| --- | --- |
| Grill / clarify | Convert vague operator asks into business constraints, affected systems, owner, SLA, risk, and approval path. |
| PRD / issue slicing | Break ERP/MES/WMS/TMS integration work into small, testable slices. |
| Triage | Route major issues by severity: shortage, excess inventory, forecast miss, supplier OTIF, quality hold, logistics delay, cash exposure. |
| Architecture improvement | Keep ontology, API, UI, and connector boundaries clear. |
| Handoff | Produce operator-ready summaries with evidence, next action, and remaining risk. |

## Autoresearch layer for prediction

The autoresearch pattern is useful for model improvement, but it must be bounded and auditable:

| Experiment type | Candidate metric | Promotion gate |
| --- | --- | --- |
| Forecast alignment | lower forecast error / fewer stockout alerts | improves baseline and does not increase false alarms |
| News risk prediction | earlier warning before ERP shortage | cites source, links affected material/supplier, reduces manual review time |
| Supplier performance | better OTIF escalation precision | improves precision on high-risk supplier actions |
| Inventory rebalance | fewer shortage/excess conflicts | preserves customer commitment and finance constraints |

Every experiment should log:

```text
run_tag
hypothesis
input dataset
model or rule change
baseline metric
candidate metric
operator impact
decision: reject / keep / promote
```

## UI implication

The simple dashboard should expose this in plain language:

- **Connect Existing Systems** shows ERP/MES/WMS/TMS/news/blockchain inputs as source systems that feed the ontology layer, not as the final user experience.
- **Power Templates** shows reusable workflows such as agent skill triage and autoresearch risk sprints.
- **Next Decision** shows the recommended action, approval status, writeback target, and proof trail.
- **Ontology Decision Map** explains why the agent connects system data to business objects.

## XPRIZE / Gemini positioning

This makes the project stronger for an AI-agent business challenge because it demonstrates:

- an AI-native operating model, not just BI charts;
- a measurable learning loop for risk prediction;
- human-governed automation for traditional systems;
- auditability through traceable receipts, decision hashes, tamper-resistant evidence, EvidenceReceipt, and optional blockchain anchoring;
- a simple operator UI that can be explained in a 3-minute demo.
