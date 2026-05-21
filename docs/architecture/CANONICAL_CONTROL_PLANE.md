# Canonical Control Plane

This repo now uses one root-level control plane for enterprise readiness.

## Source of truth
- `contracts/supply_chain_ontology.yaml`
- `contracts/action_catalog.yaml`
- `contracts/lifecycle_model.yaml`
- `governance/policy.yaml`
- `contracts/control_plane_manifest.yaml`

## What changed
- Removed embedded runtime ontology duplicates under `apps/api/app/`
- Removed embedded runtime governance duplicate under `apps/api/governance/`
- Removed duplicate `materializations` DDL from `seed/00_schema.sql`
- Runtime loaders now resolve only the canonical root contracts

## Why this matters
This keeps AI agents, API validation, approvals, and UI semantics aligned to one enterprise control plane rather than multiple drifting copies.
