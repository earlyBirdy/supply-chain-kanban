# Optional Module Boundary

This module is a packaging layer for challenge submission evidence. It is not part of the production ontology, ERP/MES connector contract, or default UI.

## Core repo remains responsible for

- supply-chain ontology
- ERP/MES/WMS/TMS source references
- AI-agent detection and recommendation loop
- human approval gates
- writeback/evidence receipts
- blockchain-ready proof layer
- simple manager UI

## Optional module is responsible for

- challenge narrative
- 90-day customer/revenue evidence checklist
- 3-minute demo script
- judge-facing proof examples
- optional business-readiness API snapshot

## Dependency rule

Core code must not import files from `optional_modules/xprize_90_day_business/`. The optional module may copy examples from core, but core cannot depend on the optional module.
