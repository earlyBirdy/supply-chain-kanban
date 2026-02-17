# Supply Chain Kanban – Demo Guide (Local)

This repo is designed to be **one-command demoable**:
- Postgres seeded with schema + demo data
- FastAPI Object Graph API (`/docs`)
- Agent loop that creates/updates cases + recommendations
- Optional Superset UI bootstrap (dashboards)

## Prerequisites
- Docker + Docker Compose
- (Optional) Python 3.11+ if you want to run the standalone agent scripts in `/agents`

## 1) Start the demo (API + agent)
From repo root:

```bash
cp .env.example .env
make demo
```

Open:
- API docs: http://localhost:8000/docs

## 2) Start the demo with Superset UI (optional)

```bash
cp .env.example .env
make demo-ui
```

Open:
- Superset UI: http://localhost:8088

Credentials come from `.env`:
- `SUPERSET_ADMIN_USER`
- `SUPERSET_ADMIN_PASS`

> Superset bootstrap runs automatically via the `superset_bootstrap` container.
> If the UI looks empty at first, give it a minute, then refresh.

## 3) What to show in a live demo
1. **Ontology**: show `/ontology` (or `/ontology/yaml`) and how objects relate
2. **Cases**: show `/cases` and how cases are created/updated by the agent loop
3. **Kinetic actions**: run `POST /actions/execute?dry_run=1` to show guardrails
4. **Governance**: show `GET /governance/policy` and policy hot-reload
5. **Audit**: show action log tables (or API endpoints, if added in later patches)

## Common issues
- API not ready yet → check `docker compose logs -f api`
- DB still initializing → check `docker compose logs -f db_init`
- Superset bootstrap still running → check `docker compose --profile ui logs -f superset_bootstrap`

## Handy commands
- Tail logs: `make logs`
- PSQL: `make psql`
- Reset DB: `make reset` (removes docker volumes)
