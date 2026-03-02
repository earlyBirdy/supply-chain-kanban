# Next steps (Gemini Live Agent + News Monitor)

This repo currently ships a **deterministic** “Gemini Live Agent” demo scaffold (good for a stable Devpost video).
This document lists the practical next steps to turn it into a *real* Live Agent that checks news regularly and runs on Google Cloud.

## 1) Replace the websocket scaffold with real Gemini Live

**Goal:** microphone audio → Gemini Live session → tool calls into this backend → streamed responses back to the browser.

Recommended implementation path:
1. Keep `live_orchestrator/` as the “edge” service that owns the Live session.
2. Add a `MODE=scaffold|gemini_live` env flag.
3. In `gemini_live` mode:
   - create a Live session using the official GenAI SDK
   - stream audio chunks from the browser (WebRTC or WS audio frames)
   - register tools that call your existing API:
     - `run_memory_leakage_burst()` (keeps deterministic demo)
     - `list_news_items(topic, limit)`
     - `list_news_alerts(topic, limit)`
     - `create_case(...)` / `append_evidence(...)` (optional)
     - `dry_run_action(...)` (recommended: human-in-the-loop)

**Guardrails (for judging):**
- default all executions to **dry-run**
- require an explicit “confirm” message before any write-back action
- always show “evidence citations” (URLs + extracted claims) alongside conclusions

## 2) Turn on real news monitoring (keep deterministic fallback)

**Goal:** check DRAM/NAND “leakage” signals periodically (RSS first), and emit evidence + alerts + cases.

Suggested steps:
1. Implement an RSS fetcher in `news_monitor/app/fetchers/` (Google News RSS is fine to start).
2. Add allowlist / blocklist rules in `news_monitor/app/sources.yaml`.
3. Dedupe by `url` (already UNIQUE in DB) and also by `(title, published_at)` similarity.
4. Convert articles → structured signals:
   - vendor (Micron/SK Hynix/Samsung/Kioxia/etc.)
   - product (HBM/DDR5/NAND/enterprise SSD)
   - direction (price down / oversupply / inventory dump / channel checks)
   - confidence score (0–100)
5. Trigger a case when score ≥ threshold (e.g., 60), otherwise store evidence only.

Keep `NEWS_MODE=deterministic|rss`, defaulting to deterministic for demos.

## 3) Production deployment on Google Cloud (Devpost)

A minimal, judge-friendly GCP deployment:
- **Cloud Run**: `agent_runtime` (API), `live_orchestrator` (Live session + tools), `web_demo` (UI)
- **Cloud SQL (Postgres)**: store cases/news/audit
- **Secret Manager**: Gemini credentials
- **Cloud Scheduler** (or Cloud Run Jobs): run `news_monitor` every N minutes

Bonus points:
- Terraform or `gcloud` scripts in `/infra`
- a short “proof of GCP” screen recording (Cloud Run services list + hitting the public URL)

## 4) Devpost 3-minute video checklist

1. Start stack: `make demo-live`
2. Open `http://localhost:8080`
3. Click **Run Memory Leakage Burst**
4. Click **Refresh Alerts** and highlight the top severity signal
5. Click **Refresh News** and show multiple evidence items
6. Open `http://localhost:8000/docs` and show:
   - `GET /news/items`
   - `GET /news/alerts`
   - `POST /demo/run_scenario`

## 5) Suggested follow-up patches (small, high impact)

- Web UI:
  - render alert list + evidence list in tables (not only JSON log)
  - show `case_id` / `card_id` created by the scenario
  - add a “Video Mode” button that runs the entire flow in sequence
- Observability:
  - add request_id propagation to orchestrator → API calls
  - add basic structured logs (json) for demo capture
