from __future__ import annotations

from fastapi import APIRouter, Query

from ...db import all

router = APIRouter()


@router.get("/recent")
def recent(limit: int = Query(50, ge=1, le=200)):
    rows = all(
        """
        SELECT
          action_id,
          case_id,
          channel,
          action_type,
          result,
          created_at,
          payload->'_audit' AS audit
        FROM agent_actions
        ORDER BY created_at DESC
        LIMIT :lim
        """,
        lim=limit,
    )
    return {"ok": True, "items": rows}


@router.get("/by_case/{case_id}")
def by_case(case_id: str, limit: int = Query(200, ge=1, le=500)):
    rows = all(
        """
        SELECT
          action_id,
          case_id,
          channel,
          action_type,
          result,
          created_at,
          payload->'_audit' AS audit
        FROM agent_actions
        WHERE case_id::text = :cid
        ORDER BY created_at DESC
        LIMIT :lim
        """,
        cid=case_id,
        lim=limit,
    )
    return {"ok": True, "case_id": case_id, "items": rows}
