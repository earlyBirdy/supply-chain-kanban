from app.rbac import can_execute


def test_can_execute_denied_when_action_not_allowed() -> None:
    policy = {"rbac": {"permissions": {"execute": {"ui": ["SomeOtherAction"]}}}}
    ok, reason = can_execute(policy, channel="ui", action_type="UpdateCardStatus", payload={"new_status": "todo"})
    assert ok is False
    assert "not permitted" in reason


def test_can_execute_operator_constraint_denies_specific_status() -> None:
    policy = {
        "rbac": {
            "permissions": {"execute": {"operator": ["UpdateCardStatus"]}},
            "channels": {"ui": "operator"},
            "constraints": {"operator_update_cardstatus": {"deny_new_status": ["resolved"]}},
        }
    }
    ok, reason = can_execute(policy, channel="ui", action_type="UpdateCardStatus", payload={"new_status": "resolved"})
    assert ok is False
    assert "cannot set card status" in reason


def test_can_execute_payload_rule_enforces_risk_threshold() -> None:
    policy = {
        "rbac": {
            "permissions": {"execute": {"ui": ["UpdateCardStatus"]}},
            "action_payload_rules": [
                {
                    "action_type": "UpdateCardStatus",
                    "when": {"new_status": "resolved"},
                    "require_risk_ge": 80,
                    "reason": "high risk only",
                }
            ],
        }
    }

    ok1, _ = can_execute(policy, channel="ui", action_type="UpdateCardStatus", payload={"new_status": "resolved"}, case_risk_score=90)
    assert ok1 is True

    ok2, reason2 = can_execute(policy, channel="ui", action_type="UpdateCardStatus", payload={"new_status": "resolved"}, case_risk_score=10)
    assert ok2 is False
    assert "payload rule" in reason2
