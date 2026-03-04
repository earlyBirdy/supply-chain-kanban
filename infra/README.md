# Infra (Cloud Run + Cloud SQL)

This folder is **optional**. The Devpost demo works fully with `docker compose --profile live up`.

Use these scripts if you want a public deployment:

- Cloud SQL (Postgres) for the agent DB
- Cloud Run for:
  - `api` (FastAPI + agent runtime)
  - `live_orchestrator` (WebSocket bridge)
  - `web_demo` (static UI)
  - `news_monitor` (cron-style poller or Cloud Run Jobs)

## Quick start (scripts)

1) Set env vars:

```bash
export PROJECT_ID="YOUR_GCP_PROJECT"
export REGION="us-central1"
export DB_INSTANCE="sck-demo-db"
export DB_NAME="sck"
export DB_USER="sck"
export DB_PASS="CHANGE_ME"
```

2) Enable APIs:

```bash
bash infra/gcloud/00_enable_apis.sh
```

3) Create Cloud SQL:

```bash
bash infra/gcloud/10_create_sql.sh
```

4) Deploy Cloud Run services:

```bash
bash infra/gcloud/20_deploy_services.sh
```

> Notes:
> - For Gemini Live mode (optional), you also need to configure credentials:
>   - Vertex AI: use ADC on Cloud Run via service account + `GOOGLE_GENAI_USE_VERTEXAI=true`
>   - Or Gemini Developer API: store `GOOGLE_API_KEY`/`GEMINI_API_KEY` in Secret Manager and mount as env var.

## Next steps (recommended)

- Replace the placeholder container builds with Cloud Build pipelines.
- Add IAP / OAuth to protect the endpoints.
- Convert `news_monitor` to Cloud Scheduler + Cloud Run Jobs for predictable polling.
