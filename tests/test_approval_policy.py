from __future__ import annotations

from app.approval import approval_required_for_action


def test_approval_required_for_explicit_list_true() -> None:
    policy = {"action_approval_policy": {"action_types_require_approval": ["TriggerPurchase"]}}
    assert approval_required_for_action(policy, action_type="TriggerPurchase", payload={}, execution_target="local_db") is True


def test_approval_not_required_for_explicit_no_list() -> None:
    policy = {"action_approval_policy": {"action_types_no_approval": ["UpdateCardStatus"]}}
    assert approval_required_for_action(policy, action_type="UpdateCardStatus", payload={"new_status": "in_progress"}, execution_target="local_db") is False


def test_external_connector_requires_approval_by_default() -> None:
    policy = {"action_approval_policy": {"external_connectors_require_approval": True}}
    assert approval_required_for_action(policy, action_type="ExpediteShipment", payload={}, execution_target="sap") is True
