from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List


def _hash_payload(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _trend_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = [
        {
            "commodity_id": "memory_hbm_dram_nand",
            "commodity": "Memory chips: HBM, DDR5/DRAM, NAND/SSD",
            "risk_level": "critical",
            "early_warning_score": 92,
            "time_horizon": "0-12 months",
            "stage": "trend_formation_before_mainstream_shortage",
            "it_defense_exposure": [
                "AI servers and edge AI boxes",
                "secure workstations and rugged computers",
                "mission computers and radar/sensor processing",
                "telecom and datacenter infrastructure",
            ],
            "weak_signals": [
                "AI datacenter demand reserves HBM and DDR5 supply years ahead",
                "memory vendors shift wafer starts toward higher-margin AI/server memory",
                "DRAM/NAND contract prices and memory-stock momentum rise before procurement headlines",
                "BOM memory cost share rises in servers, PCs, telecom, automotive, and medical devices",
            ],
            "recommended_actions": [
                "Rank SKUs by DRAM/NAND/SSD/HBM exposure",
                "Request supplier lead-time and price-validity updates now",
                "Lock critical memory supply through LTAs or allocation reservations",
                "Run margin and customer-price scenario before quote renewal",
            ],
            "human_approval_gate": "CFO or supply-chain leader approval before purchase commit, price adjustment, or customer allocation change.",
        },
        {
            "commodity_id": "advanced_packaging_abf_cowos_interposer",
            "commodity": "Advanced packaging: ABF substrate, CoWoS capacity, silicon interposers",
            "risk_level": "high",
            "early_warning_score": 86,
            "time_horizon": "3-12 months",
            "stage": "capacity_tightness",
            "it_defense_exposure": [
                "AI accelerators and high-end GPUs",
                "defense signal-processing modules",
                "HPC boards and secure datacenter nodes",
                "high-bandwidth networking ASICs",
            ],
            "weak_signals": [
                "AI accelerator demand consumes advanced packaging slots",
                "OSAT and foundry capacity additions trail demand because packaging lines take time to qualify",
                "Lead times for high-layer substrates and interposers rise before finished-card shortages",
                "Supplier comments mention packaging as the bottleneck, not only wafer supply",
            ],
            "recommended_actions": [
                "Track ABF/interposer/CoWoS exposure per board family",
                "Ask suppliers to separate wafer availability from packaging availability",
                "Create alternate board-spin or approved-equivalent substrate review",
                "Reserve packaging slots for defense/high-margin programs first",
            ],
            "human_approval_gate": "Engineering + program approval before BOM substitution or priority allocation.",
        },
        {
            "commodity_id": "critical_semiconductor_minerals",
            "commodity": "Critical semiconductor minerals: gallium, germanium, indium, tantalum",
            "risk_level": "high",
            "early_warning_score": 84,
            "time_horizon": "0-12 months",
            "stage": "geopolitical_supply_control",
            "it_defense_exposure": [
                "RF front ends and radar modules",
                "infrared optics and thermal imaging",
                "fiber optics, photonics, and satellite payloads",
                "wide-bandgap power and compound-semiconductor devices",
            ],
            "weak_signals": [
                "Export controls or licensing delays hit byproduct minerals before component shortages appear",
                "Spot premiums rise for non-China material and recycling streams",
                "Defense primes and foundries request longer visibility on mineral origin and compliance",
                "Supplier quotes add force-majeure, allocation, or country-of-origin language",
            ],
            "recommended_actions": [
                "Map gallium/germanium/indium/tantalum content to RF, optics, and power modules",
                "Add origin, licensing, and recycling-source fields to supplier portal requests",
                "Qualify secondary material sources where defense rules allow",
                "Hold safety stock for long-lifecycle defense and telecom products",
            ],
            "human_approval_gate": "Compliance + engineering approval before alternate mineral source or qualified-part substitution.",
        },
        {
            "commodity_id": "rare_earth_magnets_dy_tb_ndpr",
            "commodity": "Rare earth magnets: NdPr, dysprosium, terbium, yttrium",
            "risk_level": "high",
            "early_warning_score": 82,
            "time_horizon": "3-12 months",
            "stage": "policy_and_processing_bottleneck",
            "it_defense_exposure": [
                "drones, gimbals, and precision motors",
                "missile actuation and guidance subsystems",
                "cooling fans, pumps, and robotics",
                "radar, sonar, and high-reliability electromechanical assemblies",
            ],
            "weak_signals": [
                "Export licensing tightens around heavy rare earths used in magnets",
                "Non-China magnet capacity lags demand from defense, EV, robotics, and datacenter cooling",
                "Magnet suppliers lengthen quote validity windows or add allocation language",
                "Dy/Tb price movement rises before motor and actuator lead-time alarms",
            ],
            "recommended_actions": [
                "Identify motors, actuators, fans, and pumps with rare-earth magnet dependency",
                "Request magnet grade, Dy/Tb content, and country-of-origin from suppliers",
                "Create approved-equivalent motor and magnet-source list",
                "Reserve supply for defense and safety-critical SKUs",
            ],
            "human_approval_gate": "Program + quality approval before motor, magnet, or actuator substitution.",
        },
        {
            "commodity_id": "defense_metals_tungsten_antimony",
            "commodity": "Defense metals: tungsten and antimony",
            "risk_level": "high",
            "early_warning_score": 80,
            "time_horizon": "0-12 months",
            "stage": "stockpile_and_export_control_stress",
            "it_defense_exposure": [
                "ammunition and penetrators",
                "armor, counterweights, and ruggedized mechanisms",
                "flame retardants and cable materials",
                "infrared and night-vision related supply chains",
            ],
            "weak_signals": [
                "Scrap stockpiling and export-control changes move faster than mine/refinery capacity",
                "Defense demand competes with industrial tooling and electronics end markets",
                "Processors quote longer lead times for refined material, not only raw ore",
                "Government stockpile and refinery funding becomes an early stress indicator",
            ],
            "recommended_actions": [
                "Track tungsten/antimony content by defense program and supplier tier",
                "Separate raw-material availability from processing/refining capacity",
                "Create safety-stock targets for approved long-lead material forms",
                "Ask suppliers for origin, refinery, and scrap-recovery exposure",
            ],
            "human_approval_gate": "Defense-program manager approval before allocation, safety stock, or alternate sourcing decision.",
        },
        {
            "commodity_id": "high_reliability_passives_mlcc_tantalum",
            "commodity": "High-reliability passives: MLCC, tantalum capacitors, resistors",
            "risk_level": "medium_high",
            "early_warning_score": 74,
            "time_horizon": "6-12 months",
            "stage": "second_order_ai_defense_pull",
            "it_defense_exposure": [
                "server power delivery and networking equipment",
                "avionics and defense electronics",
                "medical devices and industrial controls",
                "rugged edge AI and sensor gateway products",
            ],
            "weak_signals": [
                "AI server builds consume high-capacitance and high-reliability passives",
                "Defense and aerospace grades cannot be swapped quickly due to qualification cycles",
                "Distributor inventory falls while book-to-bill and quote activity rise",
                "Long-life products need last-time-buy or approved alternate planning earlier than consumer SKUs",
            ],
            "recommended_actions": [
                "Classify passives by grade, voltage, capacitance, package, and qualification status",
                "Create approved alternates for high-runner MLCC and tantalum parts",
                "Watch distributor inventory and quote-validity changes weekly",
                "Open engineering review for no-substitute defense BOM lines",
            ],
            "human_approval_gate": "Engineering approval before passive substitution; buyer approval before last-time-buy or buffer increase.",
        },
    ]
    for row in rows:
        row["evidence_hash"] = _hash_payload({
            "commodity_id": row["commodity_id"],
            "score": row["early_warning_score"],
            "signals": row["weak_signals"],
            "actions": row["recommended_actions"],
        })
    return rows


def build_commodity_trend_radar() -> Dict[str, Any]:
    rows = _trend_rows()
    top = rows[:3]
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "title": "IT / Defense Commodity Trend Radar",
        "prediction_window": "coming 6-12 months",
        "principle": "Do not wait for mainstream shortage headlines. Watch weak signals from demand acceleration, supplier capacity allocation, price momentum, export controls, BOM exposure, and quote/lead-time changes.",
        "scoring_model": {
            "early_warning_score": "weighted 0-100 score",
            "factors": [
                "demand_acceleration",
                "supply_tightness",
                "price_momentum",
                "geopolitical_or_export_control_stress",
                "BOM_exposure",
                "supplier_lead_time_change",
                "news_confirmation",
            ],
            "stage_model": ["weak_signal", "trend_formation", "mainstream_news_already_late"],
        },
        "top_watchlist": top,
        "watchlist": rows,
        "agent_action_loop": [
            "ingest weak signals",
            "map signals to IT/Defense BOM exposure",
            "score shortage probability and time horizon",
            "recommend approved supplier, buffer, LTA, redesign, or substitution action",
            "require human approval",
            "create evidence receipt with trend hash",
        ],
    }
