from app.api.routers.governance import _validate_policy_strict


def _base_policy() -> dict:
    return {
        "revision": 1,
        "card_status_policy": {
            "allowed_transitions": {
                "todo": ["in_progress", "blocked"],
                "in_progress": ["blocked", "resolved"],
                "blocked": ["in_progress", "resolved"],
                "resolved": [],
            },
            "approval_gate": {"resolve": {"require_channel": "supervisor", "require_high_risk_case": True, "high_risk_threshold": 80}},
            "sla_guardrails": {"blocked_requires_reason": True, "resolved_requires_timestamp": True},
        },
        "audit": {"request": {"allowlist_headers": ["x-b3-*"], "redact_headers": ["re:^x-secret-"], "allowlist_query": ["case_id"]}},
        "rbac": {"permissions": {"execute": {"ui": ["UpdateCardStatus"]}, "approve": {"ui": ["UpdateCardStatus"]}}},
    }


def test_policy_validation_requires_card_status_policy() -> None:
    errors, warnings = _validate_policy_strict({})
    assert any("card_status_policy" in e for e in errors)
    assert warnings == [] or isinstance(warnings, list)


def test_policy_validation_warns_on_unknown_status_key() -> None:
    p = _base_policy()
    p["card_status_policy"]["allowed_transitions"]["weird"] = ["todo"]
    errors, warnings = _validate_policy_strict(p)
    assert errors == []
    assert any("unknown status key" in w for w in warnings)


def test_policy_validation_errors_on_invalid_transition_target() -> None:
    p = _base_policy()
    p["card_status_policy"]["allowed_transitions"]["todo"].append("nonsense")
    errors, _warnings = _validate_policy_strict(p)
    assert any("contains invalid status" in e for e in errors)
