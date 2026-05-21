"""Supplier portal connector stubs for enterprise demos.

This pack demonstrates that governed writeback can target a supplier-facing
workflow instead of pretending every mutation is an ERP change.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ..config import SUPPLIER_PORTAL_BASE_URL, SUPPLIER_PORTAL_CONNECTOR


@dataclass
class ExecutionResult:
    ok: bool
    message: str
    data: Dict[str, Any] | None = None


class SupplierPortalConnector:
    name: str = "base"
    pack: str = "supplier_portal"

    def execute(self, action_type: str, payload: Dict[str, Any]) -> ExecutionResult:
        raise NotImplementedError


class StubSupplierPortalConnector(SupplierPortalConnector):
    name = "supplier_portal_stub"

    def execute(self, action_type: str, payload: Dict[str, Any]) -> ExecutionResult:
        supplier = payload.get("supplier_id") or payload.get("resource_id") or "unknown_supplier"
        severity = payload.get("priority") or payload.get("severity") or "high"
        return ExecutionResult(
            ok=True,
            message=f"stub-opened supplier portal workflow for {supplier}",
            data={
                "workflow_type": action_type,
                "supplier_id": supplier,
                "severity": severity,
                "portal_case_ref": f"SUP-{str(supplier).upper()}-001",
                "base_url": SUPPLIER_PORTAL_BASE_URL,
            },
        )


class _FailClosedConnector(SupplierPortalConnector):
    def __init__(self, name: str):
        self.name = name

    def execute(self, action_type: str, payload: Dict[str, Any]) -> ExecutionResult:
        return ExecutionResult(
            ok=False,
            message=(
                f"SUPPLIER_PORTAL_CONNECTOR='{self.name}' not implemented. "
                "Set SUPPLIER_PORTAL_CONNECTOR=stub or implement a real connector."
            ),
            data={"action_type": action_type, "payload": payload, "base_url": SUPPLIER_PORTAL_BASE_URL},
        )


def get_supplier_portal_connector() -> SupplierPortalConnector:
    if SUPPLIER_PORTAL_CONNECTOR.lower() in {"stub", "mock", "demo"}:
        return StubSupplierPortalConnector()
    return _FailClosedConnector(SUPPLIER_PORTAL_CONNECTOR)
