# Kanban Operating Model

## Definition

Kanban is the regular human operating model for the Supply Chain AI Agent.

A Kanban card is a **supply-chain operating case**. Most cards are normal daily operations or controlled exceptions, such as purchase-order risk, supplier follow-up, allocation changes, shipment/container delay, inventory shortage, quality hold, or ERP writeback approval. Critical cards can be shown in crisis views without changing the underlying model.

## Why keep Kanban

Supply-chain managers, planners, buyers, logistics teams, and executives can understand Kanban quickly. On regular operating days, people need a shared board that answers:

```text
What needs attention today?
Which supplier/order/container is at risk?
What is waiting for approval?
What action is being executed?
What evidence proves the update?
Are forecasts and inventory still aligned?
Which partner KPI is causing risk?
Which cross-functional plan needs demand planning, finance, or operations input?
```

## Supply-chain leader view

Kanban is the daily operating basis, but the leader view board should also summarize management health across the whole supply chain. It is designed for a supply-chain team lead or department manager who must keep forecast, inventory, partners, and execution aligned.

The leader view should include:

```text
Forecast alignment
  demand changes, forecast accuracy, upside/downside exposure

Inventory alignment
  shortages, excess, safety stock risk, constrained parts, warehouse/plant imbalance

Partner performance
  OTIF, yield, scrap, efficiency, responsiveness, supplier aging cases

Integrated operating plan
  demand planning actions, finance cost impact, operations capacity constraints

Execution governance
  approvals waiting, writebacks in progress, receipts, audit/evidence state
```

A healthy board does not only show crises. It shows whether the operating plan is still executable.

## Daily operations card schema

Each card should show:

```text
case_id
case title
risk score
priority
affected order / PO / shipment / container / supplier / resource
customer/service impact
cost/revenue impact
root cause summary
evidence summary
recommended action
approval state
owner
SLA remaining
execution receipt
ledger/evidence proof state
```

## Professional lanes

```text
Signal Intake
Triage
Mitigation Planning
Approval Gate
Executing
Resolved / Learning
```

## Crisis view

Crisis mode is not a separate workflow. It is a filtered/high-urgency view of the same Kanban cases for professional operations during disruption.

## Crisis lanes

```text
Critical Now
At Risk <24h
Watchlist
Awaiting Approval
Recovery Actions
Stabilized
```

## Manager-agent behavior

The AI agent should behave like a supply-chain department manager:

- monitor forecast accuracy and demand-change risk
- check inventory alignment against customer commitments, safety stock, and constrained resources
- monitor partner KPIs such as OTIF, yield, scrap, efficiency, and response aging
- connect demand planning, finance, and operations into integrated operating-plan decisions
- promote cases when risk increases
- assign or suggest owners
- explain the decision in business language
- prevent unsafe execution without approval
- detect stale cases and escalation risk
- create a postmortem trail after resolution

## UX principle

The board must be understandable in one screen:

```text
Case -> Impact -> Recommendation -> Approval -> Execution -> Proof
```
