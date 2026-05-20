"""Governed writeback adapter for enterprise-style execution.

This adapter now routes actions to explicit connector packs so the demo can show
ERP, supplier portal, and ticketing as distinct governed writeback paths.
It also emits richer enterprise receipts for buyer-facing demos.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict

from .erp import get_erp_connector
from .supplier_portal import get_supplier_portal_connector
from .ticketing import get_ticketing_connector


ACTION_SPECS = {
    "ExpediteShipment": {
        "target_system": "erp.shipments",
        "connector_family": "erp",
        "approval_policy_key": "erp_high_impact",
        "receipt_type": "shipment_change",
    },
    "TriggerPurchase": {
        "target_system": "erp.purchase_orders",
        "connector_family": "erp",
        "approval_policy_key": "erp_financial_commitment",
        "receipt_type": "purchase_commitment",
    },
    "RebalanceAllocation": {
        "target_system": "erp.allocations",
        "connector_family": "erp",
        "approval_policy_key": "erp_allocation_change",
        "receipt_type": "allocation_rebalance",
    },
    "OpenSupplierTicket": {
        "target_system": "supplier.portal",
        "connector_family": "supplier_portal",
        "approval_policy_key": "supplier_external_escalation",
        "receipt_type": "supplier_escalation",
    },
    "CreateOpsTicket": {
        "target_system": "ticketing.incidents",
        "connector_family": "ticketing",
        "approval_policy_key": "ticketing_internal_coordination",
        "receipt_type": "ops_ticket",
    },
}


@dataclass
class GovernedWritebackResult:
    ok: bool
    message: str
    connector_name: str
    connector_family: str
    adapter_name: str
    target_system: str
    external_ref: str
    policy_gate: str
    approval_state: str
    approval_policy_key: str
    payload: Dict[str, Any]
    receipt: Dict[str, Any]
    connector_data: Dict[str, Any] | None = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "message": self.message,
            "connector_name": self.connector_name,
            "connector_family": self.connector_family,
            "adapter_name": self.adapter_name,
            "target_system": self.target_system,
            "external_ref": self.external_ref,
            "policy_gate": self.policy_gate,
            "approval_state": self.approval_state,
            "approval_policy_key": self.approval_policy_key,
            "payload": self.payload,
            "receipt": self.receipt,
            "connector_data": self.connector_data or {},
        }


def spec_for(action_type: str) -> Dict[str, str]:
    return ACTION_SPECS.get(
        action_type,
        {
            "target_system": "erp.unspecified",
            "connector_family": "erp",
            "approval_policy_key": "erp_default",
            "receipt_type": "generic_writeback",
        },
    )


def connector_family_for_action(action_type: str) -> str:
    return spec_for(action_type).get("connector_family", "erp")


def _connector_for(family: str):
    if family == "supplier_portal":
        return get_supplier_portal_connector()
    if family == "ticketing":
        return get_ticketing_connector()
    return get_erp_connector()


class GovernedWritebackAdapter:
    name = "governed_writeback"

    def preview(self, *, action_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        spec = spec_for(action_type)
        target = spec["target_system"]
        family = spec["connector_family"]
        connector = _connector_for(family)
        external_ref = f"SIM-{uuid.uuid4().hex[:10].upper()}"
        receipt = self._build_receipt(
            action_type=action_type,
            payload=payload,
            external_ref=external_ref,
            connector_name=connector.name,
            target_system=target,
            status="simulated",
        )
        return {
            "adapter": self.name,
            "target_system": target,
            "connector_family": family,
            "connector_name": connector.name,
            "policy_gate": "approved_action_required",
            "approval_state": "simulated",
            "approval_policy_key": spec.get("approval_policy_key", "default"),
            "external_ref": external_ref,
            "change_summary": self._change_summary(action_type, payload),
            "payload": payload,
            "receipt": receipt,
        }

    def execute(self, *, action_type: str, payload: Dict[str, Any]) -> GovernedWritebackResult:
        spec = spec_for(action_type)
        family = spec["connector_family"]
        connector = _connector_for(family)
        target = spec["target_system"]
        external_ref = f"WB-{uuid.uuid4().hex[:10].upper()}"
        result = connector.execute(action_type, payload)
        receipt = self._build_receipt(
            action_type=action_type,
            payload=payload,
            external_ref=external_ref,
            connector_name=connector.name,
            target_system=target,
            status="executed" if result.ok else "blocked",
            connector_data=result.data or {},
        )
        return GovernedWritebackResult(
            ok=bool(result.ok),
            message=result.message,
            connector_name=connector.name,
            connector_family=family,
            adapter_name=self.name,
            target_system=target,
            external_ref=external_ref,
            policy_gate="approved_action_required",
            approval_state="executed" if result.ok else "blocked",
            approval_policy_key=spec.get("approval_policy_key", "default"),
            payload=payload,
            receipt=receipt,
            connector_data=result.data or {},
        )

    def _business_owner(self, family: str) -> str:
        owners = {
            "erp": "Supply Chain Control Tower",
            "supplier_portal": "Supplier Operations Desk",
            "ticketing": "Operations Governance Office",
        }
        return owners.get(family, "Operations")

    def _build_receipt(
        self,
        *,
        action_type: str,
        payload: Dict[str, Any],
        external_ref: str,
        connector_name: str,
        target_system: str,
        status: str,
        connector_data: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        spec = spec_for(action_type)
        family = spec["connector_family"]
        resource = payload.get("resource_id") or payload.get("supplier_id") or payload.get("card_id") or "selected_object"
        change_ticket = f"CHG-{uuid.uuid4().hex[:8].upper()}"
        return {
            "receipt_type": spec.get("receipt_type", "generic_writeback"),
            "summary": self._change_summary(action_type, payload),
            "business_owner": self._business_owner(family),
            "submitted_by": ((payload.get("_actor") or {}).get("sub") or (payload.get("_actor") or {}).get("email") or "demo.user"),
            "approval_checkpoint": spec.get("approval_policy_key", "default"),
            "connector_family": family,
            "connector_name": connector_name,
            "target_system": target_system,
            "external_ref": external_ref,
            "change_ticket": change_ticket,
            "status": status,
            "timeline": {
                "submitted": "pending_approval_or_execution",
                "committed": "connector_acknowledged" if status == "executed" else "simulation_only",
            },
            "before_state": {
                "resource": resource,
                "workflow_state": "open_case",
                "governed_destination": target_system,
            },
            "after_state": {
                "resource": resource,
                "workflow_state": "writeback_recorded" if status == "executed" else "preview_ready",
                "governed_destination": target_system,
            },
            "connector_record": connector_data or {},
        }

    def _change_summary(self, action_type: str, payload: Dict[str, Any]) -> str:
        if action_type == "ExpediteShipment":
            return f"Send an expedite request for {payload.get('resource_id', 'the selected resource')} with priority {payload.get('priority', 'normal')}."
        if action_type == "TriggerPurchase":
            return f"Create a buffer-stock purchase for qty {payload.get('qty', '—')} on {payload.get('resource_id', 'the selected resource')}."
        if action_type == "RebalanceAllocation":
            return f"Rebalance inventory for {payload.get('resource_id', 'the selected resource')} across nodes."
        if action_type == "OpenSupplierTicket":
            return f"Open a supplier portal escalation for {payload.get('supplier_id', payload.get('resource_id', 'the selected supplier'))}."
        if action_type == "CreateOpsTicket":
            return f"Create an operations incident ticket for {payload.get('resource_id', 'the selected case')} in the governance queue."
        return f"Apply governed writeback for {action_type}."


def get_governed_writeback_adapter() -> GovernedWritebackAdapter:
    return GovernedWritebackAdapter()
