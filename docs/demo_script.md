# 2–3 minute demo script (LinkedIn / Devpost video)

## 0) One-liner
"We turned supply chain data tables into operational objects (Ontology), and made actions governable, auditable, and safe to execute."

## 1) Show the Ontology
- Open `/ontology`
- Point out: KanbanCard, Case, Signals, Actions, Recommendations + relationships

## 2) Pull a live Kanban card object
- `GET /objects/list/cards`
- Pick a `card_id`
- `GET /objects/card/{card_id}`

Explain: it's not a dashboard row; it is an operational object connected to the supply chain graph.

## 3) Run Nova demo (safe)
- `POST /demo/nova/run`
- Keep `dry_run=true`

Explain:
- The model proposes actions (UpdateCardStatus, ExpediteShipment, TriggerPurchase)
- The platform validates each proposal against governance policy (no writes yet)

## 4) Execute one action (optional)
- Call `POST /actions/execute` with the first proposal
- Show `action_id` returned (audit trail)

## 5) Wrap
"This is a Foundry-style supply chain execution layer — but small-team friendly."
