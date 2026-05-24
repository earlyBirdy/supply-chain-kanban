## v0.21

- Renamed the default UI identity from `Supply Chain Control Tower` to `Supply Chain AI Agent`.
- Replaced fictional vertical demo brands with consistent `Supply Chain AI Agent` labels so the UI no longer opens with unrelated Atlas/VoltStream/EdgeForge naming.
- Updated the leader dashboard copy toward `Supply Chain by AI Agent`: forecast, inventory, partner KPI, IOP, governed execution, and evidence.
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

