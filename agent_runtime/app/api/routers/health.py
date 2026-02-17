from fastapi import APIRouter, HTTPException

from ...db import wait_for_db
from ... import db as dbmod

router = APIRouter()


@router.get("/healthz")
def healthz():
    """Liveness: no DB call."""
    return {"status": "ok"}


@router.get("/health")
def health():
    """Readiness: validate DB connectivity (fast, safe)."""
    wait_for_db(max_seconds=5, sleep_seconds=0.5)
    return {"status": "ok"}


@router.get("/readyz")
def readyz():
    """Demo readiness: DB reachable AND core tables/views/extensions exist.

    This is more strict than /health (which only checks connectivity).
    """
    wait_for_db(max_seconds=5, sleep_seconds=0.5)

    # Tables that the demo flows rely on.
    critical_tables = [
        "kanban_cards",
        "agent_cases",
        "agent_actions",
        "pending_actions",
        "audit_log",
        "idempotency_keys",
    ]

    # Optional now, but we support checking views so future demo dashboards can depend on them.
    critical_views: list[str] = []

    # Extensions required by the schema.
    critical_extensions = ["pgcrypto"]

    missing_tables: list[str] = []
    missing_views: list[str] = []
    missing_extensions: list[str] = []

    # Table check
    rows = dbmod.all(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = ANY(:names)
        """,
        names=critical_tables,
    )
    found_tables = {r["table_name"] for r in rows}
    missing_tables = [t for t in critical_tables if t not in found_tables]

    # View check (skip query if empty)
    if critical_views:
        vrows = dbmod.all(
            """
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'public'
              AND table_name = ANY(:names)
            """,
            names=critical_views,
        )
        found_views = {r["table_name"] for r in vrows}
        missing_views = [v for v in critical_views if v not in found_views]

    # Extension check
    for ext in critical_extensions:
        erow = dbmod.one("SELECT extname FROM pg_extension WHERE extname=:ext", ext=ext)
        if not erow:
            missing_extensions.append(ext)

    if missing_tables or missing_views or missing_extensions:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "missing_tables": missing_tables,
                "missing_views": missing_views,
                "missing_extensions": missing_extensions,
            },
        )

    return {
        "status": "ok",
        "tables": critical_tables,
        "views": critical_views,
        "extensions": critical_extensions,
    }
