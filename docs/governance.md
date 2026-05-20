# Governance & Controls

## Canonical sources
- Ontology: `contracts/supply_chain_ontology.yaml`
- Action catalog: `contracts/action_catalog.yaml`
- Lifecycle model: `contracts/lifecycle_model.yaml`
- Runtime policy / RBAC: `governance/policy.yaml`

## Governance model
- Human approval for high-impact actions
- Typed actions only for writeback
- Full traceability: signal → case → recommendation → pending action → decision → execution
- Hot-reload policy for local demo workflows
- Aligned to enterprise guardrail expectations (RBAC, audit, idempotency, lifecycle contracts)

## Roles
- **observer**: read-only
- **operator**: low-impact execution
- **supervisor**: approvals + high-impact execution
- **system**: trusted automation / orchestrator
