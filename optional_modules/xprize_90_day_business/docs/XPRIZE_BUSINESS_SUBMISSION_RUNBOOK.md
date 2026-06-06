# XPRIZE Business Submission Runbook

This repo is positioned as a real-business demo for **Supply Chain Kanban AI**, not only a dashboard.

## Submission story

Supply Chain Kanban AI is an AI-native operating layer for supply-chain teams. It reads ERP, MES, WMS, supplier, news, and blockchain-ready evidence signals, maps them into ontology objects, detects inventory/supplier/production risks, recommends actions, requires human approval, and creates auditable writeback receipts.

## 1. Continuous AI agent

The submission demo must show an agent loop that can run continuously in production and on demand in the demo:

1. Read ERP/MES/WMS mock data.
2. Read news and risk signals.
3. Detect inventory, supplier, or production risk.
4. Create recommended actions with confidence and business impact.
5. Route human approval before simulated ERP/MES/WMS writeback.
6. Create evidence receipts with decision hashes and blockchain-ready proof.

Demo API:

```bash
curl http://localhost:8000/business_submission/
curl -X POST http://localhost:8000/business_submission/run
```

## 2. Human approval gate

The safe default is **read-only monitoring**. A Planner, CFO, or Operations manager must approve, reject, or request more evidence before any simulated ERP/MES/WMS/TMS writeback is created.

## 3. Evidence log

Each decision produces:

- agent decision log
- source-system inputs
- confidence and risk score
- decision hash
- receipt hash
- blockchain-ready proof status
- Gemini/API trace schema fields for judge review

Blockchain is used as an audit/proof layer, not as the operational database.

## 4. Revenue and customer evidence

Minimum business evidence to attach to Devpost:

- one pilot user or target customer interview
- LOI-ready scope: read-only ERP/MES/WMS import, risk board, approval-gated writeback
- pricing page or pilot offer
- one invoice, Stripe payment link, signed LOI, or paid consulting package if available

Suggested pilot offer:

> Two-week supply-chain risk cockpit setup. We connect read-only ERP/MES/WMS exports, monitor supplier/news risks, and deliver approval-gated recommendations with audit receipts.

## 5. Three-minute demo structure

1. Problem: supply-chain teams operate across fragmented systems.
2. Product: ontology-based command board.
3. Agent: continuous risk detection from ERP/MES/WMS + news.
4. Approval: planner/CFO approves or rejects the recommendation.
5. Proof: simulated writeback receipt, decision hash, blockchain-ready evidence.
6. Business: pilot package, target buyer, ROI from lower shortages/excess inventory.
