"""ERP connector interface + demo mock.

The point of Kinetic in this repo is NOT to actually integrate SAP/Oracle.
It's to define a clean, auditable execution boundary:

Kanban Card (object) -> Action (typed payload) -> Connector -> Result

In production you would implement:
- auth (OAuth/SAML/service accounts)
- idempotency keys
- change approvals
- write-back to ERP + back-sync to ontology
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ..config import ERP_CONNECTOR, ERP_BASE_URL


@dataclass
class ExecutionResult:
    ok: bool
    message: str
    data: Dict[str, Any] | None = None


class ERPConnector:
    name: str = "base"

    def execute(self, action_type: str, payload: Dict[str, Any]) -> ExecutionResult:
        raise NotImplementedError


class MockERPConnector(ERPConnector):
    name = "mock"

    def execute(self, action_type: str, payload: Dict[str, Any]) -> ExecutionResult:
        # Simulate a write-back without external dependencies.
        # This is where you'd call SAP/Oracle/etc.
        return ExecutionResult(
            ok=True,
            message=f"mock-executed {action_type}",
            data={"action_type": action_type, "payload": payload},
        )


def get_erp_connector() -> ERPConnector:
    # Simple registry: extend as real connectors are added.
    if ERP_CONNECTOR.lower() == "mock":
        return MockERPConnector()
    # Unknown connector -> fail closed
    return _FailClosedConnector(ERP_CONNECTOR)


class _FailClosedConnector(ERPConnector):
    def __init__(self, name: str):
        self.name = name

    def execute(self, action_type: str, payload: Dict[str, Any]) -> ExecutionResult:
        return ExecutionResult(
            ok=False,
            message=(
                f"ERP_CONNECTOR='{self.name}' not implemented. "
                "Set ERP_CONNECTOR=mock or implement a real connector."
            ),
            data={"action_type": action_type, "payload": payload, "base_url": ERP_BASE_URL},
        )
