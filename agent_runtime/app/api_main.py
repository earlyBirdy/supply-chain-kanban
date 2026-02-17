"""FastAPI entrypoint for Supply Chain Kanban's Object Graph API.

This is intentionally small and demo-friendly:
- exposes the Ontology (JSON/YAML)
- exposes canonical objects (Order/Shipment/Production/Case)
- provides a lightweight "neighbors" graph view
- supports Kinetic actions via a connector (mock by default)
- demo endpoints under /demo

v25: demo-readiness polish
- standardized error responses (JSON) with request_id
- request_id propagation via X-Request-Id
- logs correlated by request_id
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .logging_utils import setup_logging
from .request_context import get_request_id, reset_request_id, set_request_id

from .api.routers import (
    actions,
    audit_view,
    cases,
    demo,
    governance,
    graph,
    health,
    maintenance,
    objects,
    ontology,
    pending_actions,
)


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="Supply Chain Kanban – Object Graph API",
        version="0.1",
        description=(
            "A minimal Foundry-style API surface: ontology + object graph + kinetic actions. "
            "This is a demo scaffold (not production hardened)."
        ),
    )

    def _error_response(
        status_code: int,
        code: str,
        message: str,
        details=None,
    ) -> JSONResponse:
        rid = get_request_id()
        payload = {
            "error": {
                "code": code,
                "message": message,
                "details": details,
            },
            "request_id": rid,
        }
        resp = JSONResponse(status_code=status_code, content=payload)
        # Always echo request id for correlation.
        try:
            resp.headers["X-Request-Id"] = rid
        except Exception:
            pass
        return resp

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(_request: Request, exc: HTTPException):
        # Keep the detail as details for UI/debug; provide a stable message.
        msg = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return _error_response(
            exc.status_code,
            code=f"http_{exc.status_code}",
            message=msg,
            details=exc.detail,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(_request: Request, exc: RequestValidationError):
        return _error_response(
            422,
            code="validation_error",
            message="Invalid request",
            details=exc.errors(),
        )

    @app.middleware("http")
    async def _request_id_middleware(request: Request, call_next):
        rid = (request.headers.get("X-Request-Id") or "").strip() or str(uuid.uuid4())
        token = set_request_id(rid)
        start = time.time()

        response = None
        rethrow = None

        try:
            response = await call_next(request)
        except (HTTPException, RequestValidationError) as e:
            # Let exception handlers format the response, but keep correlation.
            rethrow = e
        except Exception:
            logging.getLogger("api").exception(
                "Unhandled exception rid=%s %s %s",
                rid,
                request.method,
                request.url.path,
            )
            response = _error_response(500, "internal_error", "Internal Server Error")
        finally:
            reset_request_id(token)

        # If we need to rethrow, log a concise line and re-raise.
        if rethrow is not None:
            logging.getLogger("api").warning(
                "Request error rid=%s %s %s",
                rid,
                request.method,
                request.url.path,
            )
            raise rethrow

        # Ensure request-id header exists for all non-exception-handler responses.
        if response is not None:
            try:
                response.headers["X-Request-Id"] = rid
            except Exception:
                pass

        logging.getLogger("api").info(
            "%s %s %s %dms",
            request.method,
            request.url.path,
            getattr(response, "status_code", 0),
            int((time.time() - start) * 1000),
        )
        return response

    # Core routers
    app.include_router(health.router)
    app.include_router(ontology.router, prefix="/ontology", tags=["ontology"])
    app.include_router(objects.router, prefix="/objects", tags=["objects"])
    app.include_router(cases.router, prefix="/cases", tags=["cases"])
    app.include_router(graph.router, prefix="/graph", tags=["graph"])
    app.include_router(actions.router, prefix="/actions", tags=["actions"])
    app.include_router(pending_actions.router, prefix="/pending_actions", tags=["pending_actions"])
    app.include_router(audit_view.router, prefix="/audit", tags=["audit"])
    app.include_router(governance.router, prefix="/governance", tags=["governance"])
    app.include_router(maintenance.router, prefix="/maintenance", tags=["maintenance"])
    app.include_router(demo.router, prefix="/demo", tags=["demo"])

    return app
