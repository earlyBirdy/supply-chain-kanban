# Google Cloud deployment (minimal)

This is a pragmatic GCP plan that meets the Devpost requirements:
- backend on Google Cloud
- uses at least one GCP service
- easy to prove in a short video

## Services
- Cloud Run: `agent_runtime` (API)
- Cloud Run: `live_orchestrator` (Gemini Live session + tools)
- Cloud Run: `web_demo` (UI)
- Cloud SQL (Postgres): database
- Secret Manager: Gemini credentials
- Cloud Scheduler (or Cloud Run Jobs): `news_monitor` periodic checks

## Environment variables
- `DATABASE_URL` (pointing to Cloud SQL)
- `GEMINI_API_KEY` (from Secret Manager)
- `MODE=scaffold|gemini_live`
- `NEWS_MODE=deterministic|rss`

## Proof checklist (for Devpost)
1. Cloud Run services list showing the 3 services
2. Cloud SQL instance overview
3. Hit public URL of `web_demo`
4. Trigger scenario and show evidence

## Notes
- Keep the deterministic scenario enabled for judging.
- For production, disable DEV-only endpoints like `/news/check-now` behind `DEV_MODE=0`.
