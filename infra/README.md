# Infra

Deployment scaffolding for the professional Supply Chain Kanban AI Agent.

Default services:

```text
apps/api            API + manager-agent runtime
apps/web            Kanban command board
apps/news_monitor   optional market-signal adapter
```

External dependencies:

```text
Postgres
ERP/WMS/TMS/SiteTrack connector credentials
Auth/JWT provider
Optional blockchain evidence endpoint
```

Keep demo helpers disabled outside local development.
