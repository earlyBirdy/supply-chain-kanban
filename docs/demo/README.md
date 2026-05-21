# Demo Guide

Use this guide for a local professional Supply Chain Kanban AI Agent demo.

For exact command details, see `docs/demo/RUN_LOCAL_UI.md`.

## Fastest browser demo

```bash
cp .env.example .env
make demo-web
```

Open:

```text
Kanban command board: http://localhost:8080
API docs:              http://localhost:8000/docs
```

## API-only demo

```bash
cp .env.example .env
make demo-min
```

Open:

```text
API docs: http://localhost:8000/docs
```

## Manager-agent demo

```bash
cp .env.example .env
make demo-agent
```

Open:

```text
Kanban command board: http://localhost:8080
API docs:              http://localhost:8000/docs
```

Use this mode to show the repo behaving like a supply-chain team lead or department manager.

## What to show

1. **Kanban command board** — risk cases by professional operations lane.
2. **Case detail** — affected order, shipment, supplier, container, or resource.
3. **Recommendation** — mitigation options and trade-offs.
4. **Approval gate** — who needs to approve and why.
5. **Execution receipt** — proof of governed writeback into ERP/WMS/TMS/supplier system.
6. **SiteTrack evidence** — physical-world location/handoff proof when available.
7. **Blockchain evidence anchor** — optional tamper-evident proof hash for audit and partner trust.
8. **Audit timeline** — request ID, actor, decision, receipt, and evidence chain.

## Common commands

```bash
make status
make logs
make seed
make down
make reset
make test
```

## Product story

This is not a generic task board. Kanban means a supply-chain risk-case operating model:

```text
Signal -> Kanban case -> Recommendation -> Approval -> Execution -> Receipt -> Audit
```
