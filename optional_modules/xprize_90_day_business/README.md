# Optional Module: XPRIZE 90-Day Real-Business Submission

This folder is intentionally optional and removable. It contains event-specific material for a 90-day AI-operated business challenge, while the main Supply Chain AI Agent repo remains focused on the reusable product: ontology, ERP/MES/WMS/TMS integration, AI-agent risk detection, governed approvals, and evidence receipts.

## Why this is isolated

Challenge material can be useful for a deadline, demo video, and judging checklist, but it should not confuse the product roadmap. Keep all submission language, judging evidence, temporary demo endpoints, and challenge-specific tests here. After the deadline, remove this folder without touching the core repo.

## Challenge fit

The optional story maps Supply Chain AI Agent to a real business operated with AI:

```text
Customer pain -> AI-operated supply-chain risk cockpit -> pilot package -> customer/revenue evidence -> agent logs -> approval receipts -> demo narrative
```

Recommended category fit: **Small Business Services** or **Entrepreneurship & Job Creation**, because the product helps SME manufacturers and supply-chain teams compete with AI-native operating workflows.

## What belongs here

- Devpost/XPRIZE submission narrative
- 3-minute video outline
- customer/revenue evidence checklist
- temporary business-readiness API snapshot
- optional UI snippet for judging mode
- challenge-specific tests or proof scripts

## What must stay out of the core product

- judging language in the main dashboard
- temporary challenge endpoint dependencies
- hard dependency on Gemini or Google Cloud for the local demo
- revenue evidence samples mixed with operational seed data

## Remove after deadline

```bash
rm -rf optional_modules/xprize_90_day_business
```

Then run:

```bash
python3 scripts/run_checks.py
pytest
```

The core product should still run because this module is not imported by the main API or dashboard.
