from __future__ import annotations

from fastapi import APIRouter

from ...agent_skills import build_agent_skill_catalog

router = APIRouter()


@router.get("/")
def get_agent_skill_catalog():
    """Agent skill and autoresearch catalog for the dashboard workbench."""
    return build_agent_skill_catalog()
