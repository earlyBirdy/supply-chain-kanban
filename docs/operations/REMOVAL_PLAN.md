# Removal / Scope Plan

## Removed from professional core

The repo no longer ships the historical hackathon and model-specific demo layers:

```text
Devpost submission docs
model-specific live orchestrator scaffolding
historical v0.6 docs
```

## Current rule

BI is kept for further usage as an optional analytics/reporting layer. Optional BI, alerting, compliance, and market-signal material belongs under:

```text
operations/
integrations/
docs/compliance/
docs/business/
```

Do not add new top-level folders for demo-only concepts.

## Professional core

```text
apps/api
apps/web
contracts
operations/governance
data/seed_sql
integrations
reports/audit evidence through API
```


## BI rule

Do not remove BI concepts from the repo. BI is not the operational system of record, but it is useful for ERP-adjacent analytics, executive reporting, historical trend review, and release demos. Keep BI assets under `operations/dashboards/`, `data/analytics_sql/`, or `docs/business/` instead of top-level product folders.
