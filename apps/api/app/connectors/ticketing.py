"""Ticketing connector stubs for enterprise demos.

This pack represents ITSM / workflow destinations such as ServiceNow or Jira.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ..config import TICKETING_BASE_URL, TICKETING_CONNECTOR


@dataclass
class ExecutionResult:
    ok: bool
    message: str
    data: Dict[str, Any] | None = None


class TicketingConnector:
    name: str = "base"
    pack: str = "ticketing"

    def execute(self, action_type: str, payload: Dict[str, Any]) -> ExecutionResult:
        raise NotImplementedError


class StubTicketingConnector(TicketingConnector):
    name = "ticketing_stub"

    def execute(self, action_type: str, payload: Dict[str, Any]) -> ExecutionResult:
        queue = payload.get("queue") or "SC-RISK"
        resource = payload.get("resource_id") or payload.get("supplier_id") or "unknown"
        return ExecutionResult(
            ok=True,
            message=f"stub-created ticket for {resource}",
            data={
                "workflow_type": action_type,
                "queue": queue,
                "resource_id": resource,
                "ticket_ref": f"INC-{str(resource).upper()}-001",
                "base_url": TICKETING_BASE_URL,
            },
        )


class _FailClosedConnector(TicketingConnector):
    def __init__(self, name: str):
        self.name = name

    def execute(self, action_type: str, payload: Dict[str, Any]) -> ExecutionResult:
        return ExecutionResult(
            ok=False,
            message=(
                f"TICKETING_CONNECTOR='{self.name}' not implemented. "
                "Set TICKETING_CONNECTOR=stub or implement a real connector."
            ),
            data={"action_type": action_type, "payload": payload, "base_url": TICKETING_BASE_URL},
        )


def get_ticketing_connector() -> TicketingConnector:
    if TICKETING_CONNECTOR.lower() in {"stub", "mock", "demo"}:
        return StubTicketingConnector()
    return _FailClosedConnector(TICKETING_CONNECTOR)
