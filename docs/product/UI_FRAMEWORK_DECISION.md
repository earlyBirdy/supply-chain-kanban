# UI Framework Decision

## Recommendation

Use a layered UI strategy:

```text
Now:       Static HTML/CSS/JavaScript in apps/web/public for the Kanban operator board
Debug:     Streamlit in apps/debug_ui for AI-agent debugging
Later:     React + Vite + TypeScript + Tailwind CSS + shadcn/ui for production UI
Observe:   Grafana later for metrics and system health
```

## Why keep the current static Kanban UI now?

The current static UI is useful because it is:

- zero frontend build step
- easy to serve through nginx
- easy for non-frontend contributors to edit
- good enough for the first professional Kanban demo

Do not migrate just for fashion. Migrate when one of these is true:

- the board needs reusable card/table/detail components
- API state, filters, optimistic updates, and loading states become hard to maintain
- role-based UI views become complex
- dashboard charts and scenario comparison need a component model
- customers expect a more polished SaaS-style UI

## Streamlit for AI-agent debug

Use Streamlit for the internal AI-agent cockpit:

```text
apps/debug_ui/streamlit_app.py
```

Best for:

```text
agent traces
recommendation debugging
approval-policy explanations
SiteTrack container events
ERP/WMS/TMS writeback receipts
blockchain proof status
scenario replay
```

Run:

```bash
pip install -r requirements-debug.txt
make debug-ui
```

Open:

```text
http://localhost:8501
```

## Best free professional production UI stack

Recommended future stack for the main operator UI:

```text
React
Vite
TypeScript
Tailwind CSS
shadcn/ui
TanStack Query
TanStack Table
Recharts
Lucide Icons
```

## Why this stack fits Supply Chain Kanban AI Agent

### React + TypeScript

Good for a case-management UI with many repeated components:

```text
RiskCaseCard
KanbanLane
ApprovalDrawer
ExecutionReceipt
AuditTimeline
SiteTrackLocationProof
ERPWritebackPanel
BlockchainEvidenceBadge
```

TypeScript should mirror API contracts and reduce frontend/backend drift.

### Vite

Vite gives a lightweight frontend build system and is suitable for a repo that should stay fast to run locally.

### Tailwind CSS

Tailwind is practical for dashboard layouts, status badges, SLA colors, risk severity, and responsive operations screens.

### shadcn/ui

shadcn/ui is a good fit for professional internal tools because it provides copy-owned components instead of a heavy black-box design system.

### TanStack Query and Table

Use TanStack Query for API fetching, retry behavior, cache invalidation, and optimistic UI around approvals/execution. Use TanStack Table for risk queues, approvals, audit events, connector receipts, and scenario comparisons.

### Recharts

Use for simple dashboard charts:

```text
risk trend
SLA exposure
approval cycle time
case aging
connector execution success
SiteTrack container handoff delay
```

## What not to use as the primary UI

### Grafana

Grafana is excellent for observability, but not for the core manager workflow. Use it for metrics, not approvals or daily Kanban decisions.

### Streamlit

Streamlit is excellent for debugging, but not the final polished multi-user operator UI.

### Full Next.js app

Next.js is powerful, but heavier than needed while the backend is already FastAPI and most screens are authenticated internal dashboards.

## Migration target tree

When ready, migrate `apps/web/` to:

```text
apps/web/
  package.json
  vite.config.ts
  tsconfig.json
  index.html
  src/
    app/
      App.tsx
      routes.tsx
    components/
      kanban/
      approvals/
      audit/
      receipts/
      sitetrack/
      blockchain/
      erp/
    lib/
      api.ts
      contracts.ts
      formatters.ts
    styles/
      globals.css
```

## Design principle

The UI must make the end-to-end management loop obvious:

```text
Signal -> Kanban case -> Recommendation -> Approval -> Execution -> Receipt -> Audit
```

Every UI framework decision should make this loop easier for a supply-chain manager to understand and operate.
