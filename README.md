# Supply Chain Kanban – AI Agent Demo Platform

This repository demonstrates how AI agents assist supply chain management by detecting emerging constraints, simulating trade-offs, and supporting governed decisions across demand, supply, logistics, and crisis scenarios.

## What this demo shows
- Early detection of supply risk using market signals (prices, indices)
- Multi-agent coordination (demand, supply, logistics)
- Scenario-based decision scoring (service, cost, risk)
- Human-in-the-loop governance with guardrails
- Board-ready and regulator-safe visibility

## What this is NOT
- Not a production deployment
- Not connected to real ERP, suppliers, or contracts
- Not fully autonomous execution

## Repo structure (simplified)
- `/demo` – runnable local demo (Docker + Python)
- `/agents` – agent logic & coordination
- `/signals` – market signal adapters
- `/dashboards` – board & crisis views
- `/governance` – audit & control artifacts
- `/docs` – architecture, agents, datasets, governance

## Quick start
```bash
cd demo
docker compose up -d
```
Then follow `/demo/README.md`.

## Audience
- Supply chain leaders
- Enterprise architects
- Risk, audit, and compliance teams
- System integrators (SI)


# supply-chain-kanban v0.1

Includes UI, Superset, Power BI, Slack alerts, Scenario Simulator.

# supply-chain-kanban v0.2

Adds AI agent logic for constraint pattern prediction (generic, product-agnostic).

# supply-chain-kanban v0.3

Adds market signal ingestion, learning dashboards, audit narratives, and agent KPI scorecards.

# supply-chain-kanban v0.4

Multi-agent coordination, regulator appendix, live market adapters, ROI tracking, board visuals.

# supply-chain-kanban v0.5

Adds agent negotiation, auto-contract triggers, supplier portals, regulatory automation, crisis simulation.

# supply-chain-kanban demo

Run a local demo showing AI agents detecting constraints, negotiating, and triggering scenarios.

# supply-chain-kanban documentation

This folder contains conceptual and governance documentation for the AI-agent-based supply chain demo.
