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
import os
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

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
    news,
    operator,
    business_submission,
    commodity_trends,
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
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

    @app.get("/", include_in_schema=False)
    async def _root():
        web_dir = Path(os.getenv("SUPPLY_CHAIN_WEB_STATIC_DIR", "/app/web"))
        index_file = web_dir / "index.html"
        if os.getenv("SUPPLY_CHAIN_SERVE_WEB", "").lower() in {"1", "true", "yes"} and index_file.exists():
            return FileResponse(index_file)
        return {
            "service": "Supply Chain Kanban API",
            "status": "ok",
            "message": "Open the simple web dashboard on http://localhost:8080 or API docs on /docs.",
            "links": {
                "web_dashboard": "http://localhost:8080",
                "api_docs": "/docs",
                "health": "/healthz",
                "demo_summary": "/demo/summary",
            },
        }

    @app.get("/favicon.ico", include_in_schema=False)
    async def _favicon() -> Response:
        return Response(status_code=204)

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

    def _include_api(prefix: str = "") -> None:
        # Core routers. The /api mirror is used by single-container demos such as Hugging Face Spaces.
        app.include_router(health.router, prefix=prefix)
        app.include_router(ontology.router, prefix=f"{prefix}/ontology", tags=["ontology"])
        app.include_router(objects.router, prefix=f"{prefix}/objects", tags=["objects"])
        app.include_router(cases.router, prefix=f"{prefix}/cases", tags=["cases"])
        app.include_router(graph.router, prefix=f"{prefix}/graph", tags=["graph"])
        app.include_router(actions.router, prefix=f"{prefix}/actions", tags=["actions"])
        app.include_router(pending_actions.router, prefix=f"{prefix}/pending_actions", tags=["pending_actions"])
        app.include_router(audit_view.router, prefix=f"{prefix}/audit", tags=["audit"])
        app.include_router(governance.router, prefix=f"{prefix}/governance", tags=["governance"])
        app.include_router(maintenance.router, prefix=f"{prefix}/maintenance", tags=["maintenance"])
        app.include_router(news.router, prefix=f"{prefix}/news", tags=["news"])
        app.include_router(operator.router, prefix=f"{prefix}/operator", tags=["operator"])
        app.include_router(business_submission.router, prefix=f"{prefix}/business_submission", tags=["business_submission"])
        app.include_router(commodity_trends.router, prefix=f"{prefix}/commodity_trends", tags=["commodity_trends"])
        app.include_router(demo.router, prefix=f"{prefix}/demo", tags=["demo"])

    _include_api("")
    _include_api("/api")

    web_dir = Path(os.getenv("SUPPLY_CHAIN_WEB_STATIC_DIR", "/app/web"))
    if os.getenv("SUPPLY_CHAIN_SERVE_WEB", "").lower() in {"1", "true", "yes"} and web_dir.exists():
        app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")

    return app


# Uvicorn default entrypoint (docker-compose uses app.api_main:app)
# Keeping this module-level symbol avoids needing --factory in dev/demo.
app = create_app()
