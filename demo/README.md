# Supply Chain Kanban – Demo Guide

This demo runs fully locally and shows how AI agents:
- detect emerging constraints,
- negotiate trade-offs,
- recommend governed decisions,
- and surface results on dashboards.

## Prerequisites
- Docker + Docker Compose
- Python 3.10+

## Step 1: Start the demo stack
```bash
docker compose up -d
```

Services started:
- PostgreSQL (demo data)
- Apache Superset (dashboards)

Superset UI:
http://localhost:8088

## Step 2: Initialize Superset (one-time)
```bash
docker exec -it supply-chain-kanban-superset-1 superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@example.com \
  --password admin

docker exec -it supply-chain-kanban-superset-1 superset db upgrade
docker exec -it supply-chain-kanban-superset-1 superset init
```

Login:
- user: admin
- password: admin

## Step 3: Run agent detection demo
```bash
python agents/run_agents.py
```

This simulates agents detecting emerging supply constraints from market price signals (e.g. memory, freight).

## Step 4: Run agent negotiation demo
```bash
python agents/negotiate.py
```

This simulates demand, supply, and logistics agents negotiating trade-offs using a bounded game-theory approach.

## What to explain during a live demo
1. Market signals move before ERP data
2. Agents detect patterns, not products
3. Decisions are scenario-based and explainable
4. Humans remain in control (no unsafe automation)

## Common issues
- Superset shows no charts → datasets not imported yet
- Connection error → ensure DB hostname is `db`, not `localhost`
- Health is `starting` → wait ~60 seconds

## Demo scope reminder
This demo is for behavior and decision logic, not scale or performance.
