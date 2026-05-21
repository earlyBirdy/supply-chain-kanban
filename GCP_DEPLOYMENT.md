# Deployment Notes

This repo's default deployable services are now:

```text
apps/api     FastAPI manager-agent runtime
apps/web     Kanban command board
apps/news_monitor optional market-signal adapter
```

The API service needs read access to:

```text
contracts/
operations/governance/policy.yaml
data/seed_sql/          only for local demo reset flows
```

Recommended production shape:

```text
Cloud Run / container service: API
Static hosting / container: Web board
Managed Postgres: case/action/audit store
Secret manager: DB URL, auth/JWT config, connector credentials
ERP/WMS/TMS/SiteTrack connectors: private network or customer-controlled adapter
```

Do not expose demo reset endpoints in shared deployments. Use `DEV_MODE=0`, verified auth, explicit CORS origins, and customer-specific connector credentials.
