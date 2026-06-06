# Release notes

## v0.26

- Kept the main UI as a one-page project-status board focused on summary KPIs, highlighted Major Issues, E2E project flow, AI Leader Dashboard, and the selected next decision.
- Moved existing-system connections into an `Integrations` subpage so ERP / WMS / MES / TMS / Supplier Portal / CSV setup does not crowd the daily project page.
- Moved Power Templates and Live Commodity News into a `Templates + news` subpage so demo/market-signal tools stay available without hiding the major issues list.
- Added simple page switching and active toolbar state for `Project status`, `Integrations`, and `Templates + news`.
- Bumped the frontend script cache key to `v0.26`.

## v0.25

- Kept the product name as `Supply Chain AI Agent` and made the UI story explicit: AI co-works with ERP, WMS, MES, TMS, supplier portals, and CSV/Excel reports.
- Added a simple `Connect Existing Systems` panel with read-only-first integration cards and governed writeback positioning.
- Added `Power Templates` so demos can quickly show commodity shock, supplier OTIF rescue, inventory rebalance, quality hold recovery, forecast/capacity, and governed-writeback capabilities.
- Added a `Live News for Commodity Arrangements` panel plus a `Track commodity news` action wired to the existing news API.
- Updated demo news signals and RSS allowlist toward commodities, battery materials, copper, memory, and freight disruption.
- Bumped the frontend script cache key to `v0.25`.

## v0.24

- Replaced the raw selected case UUID badge with a human-readable selected issue label.
- Made the board load path resilient: optional summary, executive brief, demo script, and screenshot manifest loads can no longer mark the whole dashboard as `API: error`.
- Removed visible `Load failed` copy for optional panel failures; the top board stays focused on major issues.
- Bumped the frontend script cache key to `v0.24` for Safari/Docker rebuilds.

## v0.23

- Fixed the visible `renderBrief` runtime path by keeping the renderer available to both internal and browser-global callbacks.
- Made executive and brief API calls non-fatal so an optional panel cannot flip the whole UI into `API: error`.
- Changed the page from fixed-height nested scrollers to normal document flow so dashboard blocks no longer overlap while scrolling.
- Removed the noisy visible `issues visible` status copy and replaced it with a short major-issues sorting note.
- Added no-cache handling for `/app.js` and a versioned script URL so Safari does not keep stale frontend code after Docker rebuilds.

# Release Notes

## v0.22
- Fixed the missing `renderExecutive()` frontend function that caused `API: error` after loading executive data.
- Simplified the header subtitle and board meta copy so old marketing phrases no longer distract from the working issues list.
- Moved the summary KPIs and risk-sorted Major Issues list to the top of the page.
- Hid the concept/trust rail by default to keep the first screen focused on major supply-chain issues and next actions.


- Renamed the default UI identity from `Supply Chain Control Tower` to `Supply Chain AI Agent`.
- Replaced fictional vertical demo brands with consistent `Supply Chain AI Agent` labels so the UI no longer opens with unrelated Atlas/VoltStream/EdgeForge naming.
- Updated the leader dashboard copy toward `Supply Chain AI Agent`: forecast, inventory, partner KPI, IOP, governed execution, and evidence.
- Updated tests to lock the Supply Chain AI Agent brand and prevent the old placeholder naming from returning.

## v0.20 — supply-chain brand + brief runtime fix

- Replaced the neutral Atlas placeholder with `Supply Chain AI Agent` / `SCA` for the default demo brand.
- Restored the missing web `renderBrief()` function so `loadExecutiveBrief()` no longer throws `Can't find variable: renderBrief`.
- Added web contract coverage for the default brand and one-page brief rendering.

Validation: `python3 scripts/run_checks.py` → 50 passed.

# Release Notes

## Supply Chain Kanban AI Agent — Operations Basis

This release resets the repo language from patch-oriented notes to professional release notes.

### Product positioning

Kanban is the regular supply-chain operations basis. It is used for daily planning, purchasing, supplier follow-up, logistics/container tracking, approval routing, governed execution, and audit evidence. Crisis operations is a dashboard/view over the same Kanban case model.

### Removed from professional core

```text
Devpost submission copy
Gemini/model-specific live demo scaffolding
historical v0.6 demo notes
```

### Kept for future use

```text
BI/dashboard definitions
analytics SQL
executive reporting concepts
ERP-adjacent reporting and integration docs
```

BI is kept as an optional analytics and reporting layer, similar to ERP/WMS/TMS integrations. It must not become the operational database or the main workflow.

### Running commands

Browser Kanban UI:

```bash
cp .env.example .env
make demo-web
```

Open:

```text
http://localhost:8080
http://localhost:8000/docs
```

Manager-agent mode:

```bash
cp .env.example .env
make demo-agent
```

News/market-signal mode:

```bash
cp .env.example .env
make demo-web
make demo-signals
```

Streamlit AI-agent debug cockpit:

```bash
pip install -r requirements-debug.txt
make debug-ui
```

Open:

```text
http://localhost:8501
```

Quality gate:

```bash
make test
```

### Architecture summary

```text
ERP / WMS / TMS / SiteTrack / market signals
  -> canonical events
  -> Kanban operating case
  -> AI recommendation
  -> approval gate
  -> governed execution
  -> receipt + audit / blockchain evidence
  -> Kanban command board / BI reporting view
```


## Demo-agent startup hardening

### Fixed

```text
make demo-agent -> db_init exited with status 3
```

Root cause: `00_schema.sql` created the transparency/evidence tables before `agent_cases`, but those tables declare foreign keys to `agent_cases`. PostgreSQL executes the schema top-to-bottom, so the init container could fail before API, web, and agent services were usable.

### Changed

```text
data/seed_sql/00_schema.sql
  Create agent_cases before traceability_events, evidence_receipts, and blockchain_anchors.

tests/test_seed_schema_order.py
  Add a regression guard so schema tables cannot reference foreign-key targets before those targets are created.
```

### Note

If Docker itself is not running, start Docker Desktop first. That environment issue appears as:

```text
Cannot connect to the Docker daemon
```


## Supply-chain leader view board

### Added

```text
operations/dashboards/supply_chain_leader_view.json
```

The repo now documents the Supply Chain AI Agent as a leader view board for regular management, not only crisis handling. The board tracks forecast accuracy, inventory alignment, partner KPIs, integrated operating-plan actions, approvals, governed execution receipts, and audit evidence.

### Updated concept

```text
Kanban remains the regular operations basis.
The leader view summarizes management health.
Cases open only when a metric breach requires action, approval, or governed writeback.
```

## v0.28

- Keeps v0.26 as baseline and ignores v0.27.
- Simplifies the project-status page by showing only the top 4 major issues and grouping lower-priority demo signals.
- Re-labels the KPI strip from raw total project issues to current major issues so demos do not look flooded after scenario generation.
- Adds Hugging Face Spaces Docker deployment support for a single-container public demo.
- Adds same-origin `/api/*` routing support for hosted demos while preserving local Docker Compose behavior.

## Dashboard ontology enhancement — ERP/MES AI-agent control room

- Expanded the ontology contract with source-system connectors, source-record references, BOM exposure, MES capacity constraints, S&OP exceptions, AI-agent run traces, writeback receipts, and simple UI view contracts.
- Synced canonical ontology mirrors under `contracts/` and `apps/api/app/` in both YAML and JSON.
- Added SQL seed schema support for the new dataset families and a sample ontology-enhancement payload.
- Updated the web UI copy and ontology map so users see ERP/MES traceability, BOM exposure, capacity constraints, AI-agent governance, blockchain proof, and a simpler manager-first view.
- Updated docs for the ERP/MES integration pattern, AI automation boundary, blockchain dataset model, and simple UI/UX hierarchy.
