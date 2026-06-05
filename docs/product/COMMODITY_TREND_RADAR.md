# IT / Defense Commodity Trend Radar

The Supply Chain AI Agent should not wait until commodity shortages become mainstream news. For IT and defense programs, the useful window is often **6-12 months before the headline**, when weak signals already show demand acceleration, supply tightness, export-control stress, price momentum, or BOM exposure.


## News-to-risk conversion

News is not shown as headlines. News is converted into ontology-linked risk signals. The AI agent maps each event to affected commodities, suppliers, logistics lanes, financial exposure, and recommended approval-gated actions.

News is converted into ontology-linked commodity risk signals. The AI agent maps each event to affected materials, BOM exposure, suppliers, industries, price risk, lead-time risk, and approval-gated actions.

For example, memory-chip shortage news becomes a `NewsRiskSignal` and `CommodityRiskSignal` connected to DRAM/NAND/HBM, BOM exposure, supplier commitments, industry demand, price risk, lead-time risk, and a planner-approved action packet.


## ERP/MES-compatible metadata and 人事時地物 explanation

Every news, market, supplier, price, and BOM signal must be stored with ERP/MES-compatible metadata. The AI agent does not only say “shortage risk.” It explains 人事時地物: who is affected, what changed, when the trend formed, where the risk appears, which materials/products are exposed, what source supports the signal, what confidence level it has, what price range changed, and what approval-gated action should happen next.

For a memory shortage prediction, the output should say:

```text
For the last 6 months, memory showed rising AI demand, supplier capacity shift, price momentum, stock/ETF confirmation, and BOM exposure. The news headline confirms a trend already detected earlier.
```

The explanation packet should include:

| Field | Required content |
| --- | --- |
| 人 / Who | supplier names, ERP vendor IDs, affected customers, source organizations, approval owner |
| 事 / What | demand acceleration, supplier capacity shift, price movement, lead-time change, allocation status |
| 時 / When | lookback period, signal dates, quote validity, prediction window, decision timestamp |
| 地 / Where | supplier country/region, plant, warehouse, logistics lane, customer market |
| 物 / Object | commodity family, material IDs, BOM components, SKU, PO, WO, lot/batch, product family |
| Source | source name, source type, URL/report ID/email ID, publish date, evidence hash |
| Confidence | source confidence %, extraction confidence %, model confidence %, evidence quality score |
| Price range | spot/contract/quote price range, currency, minimum/maximum, change %, valid-from/valid-to |
| ERP/MES refs | company code, plant, material number, vendor ID, PO, work order, line, warehouse/bin |
| Action | recommended action, approval owner, approval status, writeback target, action receipt |

Example evidence packet / prediction packet:

The doc must include both a short dashboard sentence and a complete machine-readable packet. The short sentence is for planners. The packet is for ERP/MES/WMS/TMS interconnection, audit, scoring, and future model training.

### Planner-facing Supply Chain Risk Review / S&OP Exception Report

The primary planner-facing report should use supply-chain language first. This is more natural for planners, procurement, S&OP, finance, and customer-commit teams than a quality-only 5 Why / 8D layout because they need to decide allocation, inventory, supplier commitment, customer risk, and margin impact. 5 Why and 8D-lite are still useful, but they should sit underneath the main risk review as the root-cause / corrective-action appendix.

#### Executive risk summary

Memory shortage risk has moved to **Stage 2 - trend formation** for the next **6-12 months**. The affected commodity family is memory: HBM, DDR5, DRAM, NAND, and SSD. The affected business areas are AI data center, IT, automotive, telecom, medical device, defense electronics, and rugged edge systems.

For the last 6 months, memory showed rising AI demand, supplier capacity shift, price momentum, stock/ETF confirmation, supplier quote changes, lead-time risk, and BOM exposure. The news headline confirms a trend already detected earlier.

#### Supply Chain Risk Review fields

| Field | Planner question | Memory example | Required metadata / evidence |
| --- | --- | --- | --- |
| Signal | What changed before the headline? | AI data center demand, HBM/DDR5 pressure, DRAM/NAND price momentum, supplier quote validity shortened | source IDs, signal dates, source confidence %, extraction confidence % |
| Risk | What risk is forming? | Memory moved from Watch to Stage 2 - trend formation | risk stage, early-warning score, model confidence, prediction window |
| Exposure | What do we actually use? | DDR5, NAND, SSD, DRAM in edge AI boxes and rugged servers | ERP material IDs, BOM IDs, SKU IDs, PO/WO, supplier IDs |
| Business impact | What happens if we do nothing? | Lead time may extend from 60-75 days to 90-120 days; BOM cost may rise 12-28% | inventory days, safety stock, quote price range, margin exposure, customer/order impact |
| Scenario | What are base/risk/worst cases? | Base: price rises; Risk: allocation starts; Worst: shortage affects customer commits | scenario assumptions, probability, affected plant/lane/customer market |
| Options | What choices do planners have? | monitor, lock supply, buffer stock, qualify alternate vendor, adjust customer price | action catalog ID, cost/working-capital impact, implementation lead time |
| Recommendation | What should be approved now? | Lock critical DDR5/NAND/SSD supply and run margin impact scenario | approval owner, writeback target, action receipt |
| Follow-up trigger | When do we escalate? | LT >120 days, quote validity <7 days, price increase >30%, safety stock <45 days | trigger thresholds, monitoring cadence, owner |

#### Scenario planning example

| Scenario | Meaning | Trigger | Action |
| --- | --- | --- | --- |
| Base case | Prices rise but supply remains available | DRAM/NAND +10-20%, LT <=90 days | monitor weekly, update forecast and margin model |
| Risk case | Lead time extends and supplier allocation begins | LT 90-120 days, quote validity 7-14 days | lock critical supply, raise safety stock, open supplier review task |
| Worst case | Allocation / shortage affects customer commits | LT >120 days or allocation status constrained | customer allocation plan, alternate source qualification, executive approval |

#### Supporting RCA appendix: 5 Why

| Why | Explanation | Evidence required |
| --- | --- | --- |
| Why 1 | Why is memory shortage risk rising? AI data center demand is increasing HBM and DDR5/server memory consumption. | demand acceleration signal, market report, customer forecast, AI server buildout indicator |
| Why 2 | Why does this affect normal supply chains? Memory suppliers are shifting capacity and priority toward higher-margin HBM/server memory. | supplier capacity comment, allocation note, supplier guidance, quote response |
| Why 3 | Why does it become visible in price? DRAM/NAND contract prices, supplier quotes, and quote-validity windows are moving against buyers. | contract/spot/quote price range, valid-from/valid-to period, RFQ/PO evidence |
| Why 4 | Why does it affect our products? ERP/BOM/PLM mapping shows DDR5, NAND, SSD, or HBM exposure in key SKUs and work orders. | ERP material ID, BOM ID, SKU, PO, WO, WMS inventory days, safety stock |
| Why 5 | Why does the headline matter now? The headline is confirmation; weak signals were already detected over the prior six months. | signal timeline, first weak-signal date, trend-formation date, headline-confirmation date |

#### Supporting corrective-action appendix: 8D-lite

| 8D item | Supply Chain AI output | Required metadata / evidence |
| --- | --- | --- |
| D1 Team / Owner | Procurement manager, planner, supplier manager, finance owner, quality/MES owner | approval owner, escalation owner, business function |
| D2 Problem | Memory shortage risk moved from weak signal to trend formation | commodity, materials, affected industries, prediction window, model confidence |
| D3 Containment | Review inventory, request updated lead time, hold non-critical spot buys, check allocation risk | WMS inventory days, safety stock days, supplier lead time, quote validity |
| D4 Root cause | AI demand acceleration + supplier capacity shift + price momentum + BOM exposure | 5 Why chain, source confidence %, extraction confidence %, evidence quality score |
| D5 Corrective action | Lock critical supply, qualify alternates, update BOM risk register, run margin scenario | ERP PR/PO target, supplier review task, BOM risk register, finance scenario |
| D6 Validate action | Confirm supplier allocation, updated price validity, PO coverage, safety stock, and lead-time reduction | supplier commitment, PO confirmation, inventory coverage, validation date |
| D7 Prevent recurrence | Add commodity to radar, monitor weak signals, automate monthly review, maintain alternate AVL/AML | radar rule ID, watchlist owner, review cadence, AVL/AML status |
| D8 Evidence / closure | Attach evidence packet, decision hash, approval receipt, writeback log, optional blockchain-ready anchor | evidence_hash, decision_hash, action_receipt_id, writeback receipt |


```json
{
  "prediction_id": "pred_memory_2026_06_001",
  "schema_version": "commodity_prediction_packet.v1",
  "commodity_family": "memory",
  "materials": ["HBM", "DDR5", "DRAM", "NAND", "SSD"],
  "prediction_window": "6-12 months",
  "lookback_period": {
    "start": "2025-12-01",
    "end": "2026-06-01",
    "label": "last_6_months"
  },
  "human_context": {
    "人": {
      "suppliers": ["Micron", "Samsung", "SK Hynix"],
      "erp_vendor_ids": ["VENDOR_MEMORY_001", "VENDOR_MEMORY_002"],
      "affected_customers": ["CUSTOMER_AI_EDGE_01", "CUSTOMER_DEFENSE_02"],
      "affected_industries": [
        "AI data center",
        "IT",
        "automotive",
        "medical devices",
        "telecom",
        "defense electronics"
      ],
      "approval_owner": "procurement_manager"
    },
    "事": {
      "detected_trend": "Memory shortage risk moved from weak signal to trend formation.",
      "drivers": [
        "AI demand increased",
        "supplier capacity shifted toward HBM/server memory",
        "DRAM/NAND price momentum increased",
        "stock/ETF confirmation strengthened",
        "BOM exposure confirmed in ERP/PLM data",
        "supplier quote validity shortened",
        "lead-time risk increased"
      ]
    },
    "時": {
      "trend_observed_for": "last 6 months",
      "signal_start": "2025-12",
      "first_weak_signal_date": "2025-12-15",
      "trend_formation_date": "2026-03-15",
      "headline_confirmation_date": "2026-06-03",
      "quote_validity_window": "7-14 days",
      "expected_shortage_window": "2026-H2 to 2027-H1"
    },
    "地": {
      "supplier_regions": ["Taiwan", "Korea", "Japan", "US"],
      "affected_plants": ["PLANT_TW_01", "PLANT_TH_01"],
      "affected_warehouses": ["WH_TW_MEMORY", "WH_TH_EDGE"],
      "logistics_lanes": ["KR->TW", "TW->TH", "JP->TW"],
      "customer_markets": ["US", "Taiwan", "Thailand", "EU"]
    },
    "物": {
      "erp_material_ids": ["MAT_DDR5_32G", "MAT_NAND_512G", "MAT_SSD_1TB"],
      "bom_ids": ["BOM_EDGE_AI_BOX_V1", "BOM_SERVER_BOARD_V2"],
      "sku_ids": ["SKU_EDGE_AI_BOX", "SKU_RUGGED_SERVER"],
      "purchase_orders": ["PO_2026_00091"],
      "work_orders": ["WO_2026_0601_001"],
      "lots_or_batches": ["LOT_MEMORY_2026_06_A"],
      "product_families": ["rugged edge AI", "server board", "telecom gateway"]
    }
  },
  "erp_mes_wms_tms_mapping": {
    "erp": {
      "company_code": "COMPANY_001",
      "plant": "PLANT_TW_01",
      "purchasing_org": "PORG_TW",
      "purchasing_group": "PG_MEMORY",
      "material_numbers": ["MAT_DDR5_32G", "MAT_NAND_512G"],
      "vendor_ids": ["VENDOR_MEMORY_001"],
      "purchase_orders": ["PO_2026_00091"],
      "currency": "USD",
      "incoterms": "FOB"
    },
    "mes": {
      "factory": "FACTORY_TH_01",
      "line": "LINE_EDGE_AI_02",
      "work_orders": ["WO_2026_0601_001"],
      "process_step": "SMT + final assembly",
      "wip_lots": ["LOT_MEMORY_2026_06_A"],
      "yield_risk": "medium"
    },
    "wms": {
      "warehouse": "WH_TH_EDGE",
      "bin_locations": ["BIN_MEMORY_A01"],
      "inventory_days": 45,
      "safety_stock_days": 60,
      "allocation_status": "watch"
    },
    "tms": {
      "origin": "KR",
      "destination": "TH",
      "lane_id": "LANE_KR_TW_TH_MEMORY",
      "carrier": "CARRIER_001",
      "eta_risk": "medium"
    }
  },
  "price_ranges": [
    {
      "indicator": "DRAM contract price",
      "period": "last_6_months",
      "change_range_pct": "15-35%",
      "min_change_pct": 15,
      "max_change_pct": 35,
      "currency": "USD",
      "valid_from": "2025-12-01",
      "valid_to": "2026-06-01",
      "source_confidence": 0.78
    },
    {
      "indicator": "NAND contract price",
      "period": "last_6_months",
      "change_range_pct": "10-25%",
      "min_change_pct": 10,
      "max_change_pct": 25,
      "currency": "USD",
      "valid_from": "2025-12-01",
      "valid_to": "2026-06-01",
      "source_confidence": 0.72
    },
    {
      "indicator": "supplier_quote_memory_parts",
      "period": "latest_RFQ",
      "change_range_pct": "12-28%",
      "min_change_pct": 12,
      "max_change_pct": 28,
      "currency": "USD",
      "quote_valid_until": "2026-06-14",
      "source_confidence": 0.90
    },
    {
      "indicator": "stock_or_etf_confirmation",
      "period": "last_6_months",
      "signal": "memory supplier / ETF momentum rising",
      "source_confidence": 0.76
    }
  ],
  "sources": [
    {
      "source_id": "SRC_TRENDFORCE_MEMORY_2026_001",
      "source_type": "market_report",
      "source_name": "TrendForce",
      "publish_date": "2026-05-30",
      "signal": "DRAM/NAND price momentum and HBM demand pressure",
      "url_or_report_id": "internal_or_external_report_reference",
      "source_confidence": 0.84,
      "extraction_confidence": 0.81,
      "evidence_quality_score": 0.83
    },
    {
      "source_id": "SRC_REUTERS_MEMORY_2026_001",
      "source_type": "news",
      "source_name": "Reuters",
      "publish_date": "2026-06-03",
      "signal": "industry groups warning about memory-chip supply imbalance",
      "url_or_report_id": "news_reference",
      "source_confidence": 0.82,
      "extraction_confidence": 0.79,
      "evidence_quality_score": 0.80
    },
    {
      "source_id": "SRC_INTERNAL_RFQ_2026_0601",
      "source_type": "erp_supplier_quote",
      "source_name": "internal_RFQ_PO_data",
      "publish_date": "2026-06-01",
      "signal": "supplier quote increase and shorter price-validity window",
      "source_confidence": 0.90,
      "extraction_confidence": 0.88,
      "evidence_quality_score": 0.89
    },
    {
      "source_id": "SRC_INTERNAL_BOM_2026_0601",
      "source_type": "bom_plm",
      "source_name": "internal_BOM_mapping",
      "publish_date": "2026-06-01",
      "signal": "memory dependency found in key products",
      "source_confidence": 0.92,
      "extraction_confidence": 0.90,
      "evidence_quality_score": 0.91
    }
  ],
  "planner_report": {
    "format": "supply_chain_risk_review_with_5why_8d_lite",
    "primary_view": "Supply Chain Risk Review / S&OP Exception Report",
    "executive_summary": "For the last 6 months, memory showed rising AI demand, supplier capacity shift, price momentum, stock/ETF confirmation, supplier quote changes, lead-time risk, and BOM exposure. The news headline confirms a trend already detected earlier.",
    "risk_review": {
      "signal": "AI data center demand, HBM/DDR5 pressure, DRAM/NAND price momentum, supplier quote validity shortened.",
      "risk": "Memory moved from Watch to Stage 2 - trend formation.",
      "exposure": ["MAT_DDR5_32G", "MAT_NAND_512G", "BOM_EDGE_AI_BOX_V1", "SKU_RUGGED_SERVER"],
      "business_impact": "Lead time may extend from 60-75 days to 90-120 days; supplier quote memory parts may rise 12-28%.",
      "scenario_planning": {
        "base_case": "prices rise but supply remains available",
        "risk_case": "lead time extends and supplier allocation begins",
        "worst_case": "allocation or shortage affects customer commits"
      },
      "options": ["monitor_weekly", "lock_critical_supply", "build_buffer_stock", "qualify_alternate_supplier", "adjust_customer_price"],
      "recommendation": "Lock critical DDR5/NAND/SSD supply and run margin impact scenario before the next S&OP review.",
      "follow_up_triggers": ["lead_time_gt_120_days", "quote_validity_lt_7_days", "price_increase_gt_30_pct", "safety_stock_lt_45_days"]
    },
    "rca_appendix": {
      "format": "5why_8d_lite",
      "five_why": [
      {
        "why": 1,
        "question": "Why is memory shortage risk rising?",
        "answer": "AI data center demand is increasing HBM and DDR5/server memory consumption.",
        "evidence_refs": ["SRC_TRENDFORCE_MEMORY_2026_001"]
      },
      {
        "why": 2,
        "question": "Why does this affect normal supply chains?",
        "answer": "Memory suppliers are shifting capacity and priority toward higher-margin HBM/server memory.",
        "evidence_refs": ["SRC_TRENDFORCE_MEMORY_2026_001", "SRC_INTERNAL_RFQ_2026_0601"]
      },
      {
        "why": 3,
        "question": "Why does it become visible in price?",
        "answer": "DRAM/NAND contract prices, supplier quotes, and quote-validity windows are moving against buyers.",
        "evidence_refs": ["SRC_INTERNAL_RFQ_2026_0601"]
      },
      {
        "why": 4,
        "question": "Why does it affect our products?",
        "answer": "ERP/BOM mapping shows DDR5, NAND, and SSD exposure in key SKUs and work orders.",
        "evidence_refs": ["SRC_INTERNAL_BOM_2026_0601"]
      },
      {
        "why": 5,
        "question": "Why does the headline matter now?",
        "answer": "The headline confirms a trend already detected from six months of weak signals.",
        "evidence_refs": ["SRC_REUTERS_MEMORY_2026_001"]
      }
      ],
      "eight_d_lite": {
        "D1_team_owner": ["procurement_manager", "planner", "supplier_manager", "finance_owner", "quality_mes_owner"],
        "D2_problem": "Memory shortage risk moved from weak signal to trend formation.",
        "D3_containment": ["review_inventory", "request_supplier_lead_time_update", "hold_non_critical_spot_buys"],
        "D4_root_cause": "AI demand acceleration plus supplier capacity shift plus price momentum plus BOM exposure.",
        "D5_corrective_action": ["lock_critical_supply", "qualify_alternates", "update_BOM_risk_register", "run_margin_scenario"],
        "D6_validate_action": ["confirm_supplier_allocation", "confirm_price_validity", "confirm_PO_coverage", "confirm_safety_stock"],
        "D7_prevent_recurrence": ["add_memory_to_commodity_radar", "monitor_monthly_weak_signals", "maintain_alternate_AVL_AML"],
        "D8_evidence_closure": ["evidence_hash", "decision_hash", "action_receipt_id", "writeback_receipt"]
      }
    }
  },
  "ai_prediction": {
    "early_warning_score": 87,
    "risk_stage": "Stage 2 - trend formation",
    "model_confidence": 0.82,
    "combined_confidence": 0.84,
    "explanation": "For the last 6 months, memory showed rising AI demand, supplier capacity shift, price momentum, stock/ETF confirmation, and BOM exposure. The news headline confirms a trend already detected earlier.",
    "recommended_actions": [
      "Request updated supplier lead times",
      "Lock critical DDR5/NAND/SSD supply",
      "Run margin impact scenario",
      "Qualify alternate memory suppliers",
      "Create approval-gated procurement action"
    ],
    "requires_human_approval": true,
    "approval_owner": "procurement_manager",
    "writeback_target": [
      "ERP_purchase_request",
      "supplier_review_task",
      "BOM_risk_register",
      "WMS_safety_stock_review"
    ]
  },
  "evidence": {
    "evidence_hash": "sha256:evidence_packet_hash",
    "decision_hash": "sha256:agent_decision_hash",
    "action_receipt_id": "receipt_memory_2026_06_001",
    "blockchain_anchor_status": "ready_not_required_by_default"
  }
}
```

Minimum acceptance rule: a shortage prediction is not complete unless it includes the short explanation, planner-facing Supply Chain Risk Review / S&OP Exception Report, supporting 5 Why + 8D-lite appendix, the full 人事時地物 packet, ERP/MES/WMS/TMS keys, sources with confidence percentages, time period, price ranges, affected materials/BOM/SKU/PO/WO, approval owner, writeback target, and evidence hashes.

## Shortage watchlist for the coming 6-12 months

The radar starts with six commodity families that can affect IT and defense programs:

1. **Memory chips: HBM, DDR5/DRAM, NAND/SSD**
   - Why: AI datacenters reserve HBM and server memory capacity, pulling supply from commodity DRAM/NAND and edge/industrial/server products.
   - Watch: HBM allocation, DDR5 contract prices, NAND/SSD pricing, Micron/SK hynix/Samsung guidance, memory ETF momentum, supplier quote validity.
   - Actions: map BOM memory exposure, lock critical supply, request lead-time updates, and run margin/customer-price scenarios.

2. **Advanced packaging: ABF substrate, CoWoS, silicon interposers**
   - Why: AI accelerators, HPC, radar/sensor processing, and high-bandwidth networking compete for qualified packaging capacity.
   - Watch: foundry/OSAT packaging comments, substrate lead times, interposer constraints, and GPU/accelerator launch reservations.
   - Actions: separate wafer risk from packaging risk, reserve packaging slots, and prepare approved-equivalent substrate plans.

3. **Critical semiconductor minerals: gallium, germanium, indium, tantalum**
   - Why: compound semiconductor, RF, photonics, infrared, satellite, and wide-bandgap power devices depend on minerals exposed to export controls and byproduct-processing bottlenecks.
   - Watch: export licenses, non-China premiums, recycling supply, compliance language in supplier quotes, and material-origin disclosure.
   - Actions: map mineral dependency to modules, request origin data, qualify secondary sources, and hold safety stock for long-lifecycle products.

4. **Rare earth magnets: NdPr, dysprosium, terbium, yttrium**
   - Why: drones, gimbals, motors, actuators, cooling systems, robotics, radar/sonar assemblies, and precision electromechanical systems need magnet materials and processing capacity.
   - Watch: Dy/Tb/NdPr pricing, magnet export licenses, non-China magnet capacity, and quote-validity changes.
   - Actions: identify motor/magnet dependencies, collect magnet-grade data, create approved-equivalent motor lists, and reserve material for safety-critical SKUs.

5. **Defense metals: tungsten and antimony**
   - Why: defense demand, export controls, scrap stockpiling, and limited refining capacity can stress ammunition, armor, mechanisms, flame retardants, cable materials, and night-vision adjacent supply chains.
   - Watch: scrap flows, export-control changes, refinery lead time, government stockpile activity, and processor quote language.
   - Actions: separate raw-material availability from processing capacity, map program exposure, and set safety-stock targets for approved material forms.

6. **High-reliability passives: MLCC, tantalum capacitors, resistors**
   - Why: AI servers, networking equipment, avionics, defense electronics, medical devices, and rugged edge systems consume high-reliability passives, while defense/aerospace qualification cycles slow substitution.
   - Watch: distributor inventory, book-to-bill, quote validity, lead time, and no-substitute BOM lines.
   - Actions: classify passives by grade and package, create approved alternates, and open engineering review for no-substitute lines.

## Scoring model

```text
Early Warning Score =
  demand acceleration
+ supply tightness
+ price momentum
+ geopolitical/export-control stress
+ BOM exposure
+ supplier lead-time change
+ news confirmation
```

The stage model is:

```text
weak signal -> trend formation -> mainstream news already late
```

## Agent loop

```text
ingest weak signals
-> map signals to IT/Defense BOM exposure
-> score shortage probability and time horizon
-> recommend supplier, buffer, LTA, redesign, or substitution action
-> require human approval
-> create evidence receipt with trend hash
```

## Product rule

News should be treated as **confirmation**, not the first alert. The agent should surface the trend before mainstream headlines by combining prices, supplier comments, capacity allocation, export controls, market momentum, and BOM exposure.
