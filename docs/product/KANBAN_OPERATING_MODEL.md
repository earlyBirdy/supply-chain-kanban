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
```

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
