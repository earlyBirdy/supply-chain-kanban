# Simple Overall Supply Chain Status UI

The dashboard should manage supply-chain status like an operator control room, not like a raw ERP/MES table dump.

## Default page order

1. **Overall Supply Chain Status** — one answer first: are we OK, blocked, or waiting for approval?
2. **Next Best Action** — issue, affected object, recommended action, approval owner, target system, and proof.
3. **Major Issues** — top four high-risk / approval / blocked issues only.
4. **Project E2E Flow** — supplier status → IQC → assembly → test → packing → OQC.
5. **AI Leader Dashboard** — forecast, inventory, partner KPI, and IOP actions.
6. **Drill-down subpages** — integrations, ontology map, templates, news, radar, and source catalog.

## UX contract

The default screen must answer five questions without requiring the user to understand the ontology:

- Are we OK?
- What changed since the last check?
- What action is recommended?
- Who approves it?
- What proof will be attached?

Raw ERP/MES/WMS/TMS records, raw RSS feeds, and model internals stay behind drill-down cards. The default user experience shows business decisions.

## Dynamic AI-agent improvement loop

Live commodity/news rows now feed three surfaces:

```text
news ingest/check-now
  -> Commodity Arrangement Desk
  -> Commodity Trend Radar score + live confirmation
  -> Dynamic Autoresearch Queue
```

The agent may update score, summary, source confidence, price range, BOM exposure, arrangement recommendation, and evidence hash. It may not write back to ERP/MES/WMS/TMS without human approval.

## Simple operator cards

Each overall-status card should be short enough for a daily meeting:

- Health
- Major issues
- Approvals
- Ready / blocked
- Proof
- News/radar

Each next-action card should show:

- Next best action
- Approval owner
- Proof

## Source and proof behavior

Dynamic source coverage is shown as a source catalog, not a headline list. Sources can be RSS, market API, supplier portal note, manual analyst research, or ERP/MES exception context. Every converted commodity arrangement carries source confidence, time period, price range, BOM exposure, approval owner, and proof hash.
