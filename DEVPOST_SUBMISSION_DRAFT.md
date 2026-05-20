# Devpost submission draft

## Project title
Supply Chain Kanban Live

## Tagline
A Gemini Live-style supply-chain risk agent that turns memory-market signals into grounded alerts, cases, and safe next actions.

## Elevator pitch
Supply Chain Kanban Live helps operators react to AI infrastructure supply-chain shocks faster. It watches memory-market signals, grounds the strongest risk in evidence, creates or updates a case and kanban card, and recommends the next operational step with traceability.

## Problem
AI data-center supply chains are exposed to fast-moving signals: DRAM/NAND leakage reports, pricing pressure, inventory shocks, and supplier constraints. Teams often detect these too late because the evidence is scattered across news, dashboards, tickets, and approvals.

## Solution
We built a Gemini Live-style operations agent that converts fragmented signals into a single grounded workflow:

**news + signals → alert → case → recommendation → pending action**

The demo focuses on a repeatable **Memory Leakage Watch** scenario for judging. A user can trigger the scenario, inspect the strongest alert and evidence, then ask the agent what changed and what operations should do next.

## Why Gemini Live
Gemini Live is the ideal interaction layer for this use case because supply-chain operators need a fast conversational briefing surface, not another dashboard.

It lets us:
- brief operators in natural language
- keep answers grounded in evidence and live state
- move quickly from explanation to action
- preserve human approval before execution

## Key features
- deterministic judge mode for repeatable demos
- grounded responses with evidence labels and links
- visible `case_id` and `card_id` traceability
- ranked recommendation / pending action flow
- ontology + object graph API behind the UI
- optional Gemini Live bridge path for future streaming sessions

## How it works
1. The news monitor generates or ingests memory-risk evidence.
2. Alerts are created and ranked.
3. The system opens or updates a supply-chain case.
4. A kanban card tracks the operational object.
5. The live agent summarizes the change, shows evidence, and recommends the next safe action.

## Stack
- FastAPI
- Postgres
- Docker Compose
- lightweight judge-facing web demo
- Gemini Live scaffold/bridge
- ontology/object graph contracts for traceable operations

## What makes this different
This is not just a chatbot on top of supply-chain data. The agent is connected to operational objects and action flows. It understands alerts, cases, cards, and proposed actions, and it presents them in a judge-friendly, grounded workflow.

## Current status
The current submission uses deterministic demo mode for reliable judging and includes an optional Gemini Live bridge. The next step is upgrading the orchestrator to a full streaming Gemini Live session with richer multimodal interaction.

## Demo flow
- Click **Judge Mode**
- See top alert, evidence, case/card IDs, action, and confidence
- Ask the three canned questions
- Open the API docs to show traceability and system depth

## Impact
A tool like this can shorten the time from weak market signal to operational response. That matters when supply constraints ripple through AI infrastructure planning, procurement, and production.
