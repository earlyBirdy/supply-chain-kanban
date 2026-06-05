from __future__ import annotations

from fastapi import APIRouter

from ...business_submission import build_business_submission_snapshot

router = APIRouter()


@router.get("/")
def get_business_submission_snapshot():
    """XPRIZE/Devpost business-readiness snapshot for the demo UI and judges."""
    return build_business_submission_snapshot()


@router.post("/run")
def run_business_submission_agent_once():
    """Run one deterministic demo cycle of the continuous supply-chain AI agent."""
    data = build_business_submission_snapshot()
    data["run_mode"] = "on_demand_demo_cycle"
    return data
