from fastapi import APIRouter, HTTPException, Query

from ...db import one, all

router = APIRouter()


@router.get("/")
def list_cases(
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500),
):
    if status:
        return all(
            """
            SELECT * FROM agent_cases
            WHERE status=:st
            ORDER BY updated_at DESC
            LIMIT :lim
            """,
            st=status,
            lim=limit,
        )
    return all(
        """
        SELECT * FROM agent_cases
        ORDER BY updated_at DESC
        LIMIT :lim
        """,
        lim=limit,
    )


@router.get("/{case_id}")
def get_case(case_id: str):
    r = one("SELECT * FROM agent_cases WHERE case_id=:cid", cid=case_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    return r


@router.get("/{case_id}/recommendations")
def get_recommendations(case_id: str):
    # Keep rank ordering stable
    recs = all(
        """
        SELECT * FROM agent_recommendations
        WHERE case_id=:cid
        ORDER BY rank ASC
        """,
        cid=case_id,
    )
    return {"case_id": case_id, "recommendations": recs}


@router.get("/{case_id}/scenarios")
def get_scenarios(case_id: str):
    sc = all(
        """
        SELECT * FROM agent_scenarios
        WHERE case_id=:cid
        ORDER BY created_at DESC
        """,
        cid=case_id,
    )
    return {"case_id": case_id, "scenarios": sc}


@router.get("/{case_id}/actions")
def get_actions(case_id: str):
    acts = all(
        """
        SELECT * FROM agent_actions
        WHERE case_id=:cid
        ORDER BY created_at DESC
        """,
        cid=case_id,
    )
    return {"case_id": case_id, "actions": acts}


@router.get("/{case_id}/pending_actions")
def get_pending_actions(case_id: str):
    pa = all(
        """
        SELECT * FROM v_pending_actions
        WHERE case_id=:cid
        ORDER BY updated_at DESC, rank ASC
        """,
        cid=case_id,
    )
    return {"case_id": case_id, "pending_actions": pa}
