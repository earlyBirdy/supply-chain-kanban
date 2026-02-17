from __future__ import annotations

from typing import Any, Dict


def approval_required_for_action(
    policy: Dict[str, Any],
    *,
    action_type: str,
    payload: Dict[str, Any],
    execution_target: str,
) -> bool:
    """Policy-aware approval requirement inference.

    Rules (in order):
      1) action_types_no_approval => False
      2) action_types_require_approval => True
      3) UpdateCardStatus: resolving inherits card_status_policy approval gate
      4) external_connectors_require_approval and target != local_db => True
      5) default => False
    """
    ap = (policy or {}).get("action_approval_policy") or {}
    at = (action_type or "").strip()

    no_list = set(ap.get("action_types_no_approval") or [])
    yes_list = set(ap.get("action_types_require_approval") or [])

    if at in no_list:
        return False
    if at in yes_list:
        return True

    if at == "UpdateCardStatus":
        ns = str((payload or {}).get("new_status") or "").strip()
        if ns == "resolved":
            gate = ((policy or {}).get("card_status_policy") or {}).get("approval_gate") or {}
            resolve_gate = gate.get("resolve") or {}
            # If the gate exists (typical), require approval.
            return bool(resolve_gate.get("require_channel") or resolve_gate.get("require_high_risk_case") or True)
        return False

    if bool(ap.get("external_connectors_require_approval", True)) and execution_target != "local_db":
        return True

    return False
