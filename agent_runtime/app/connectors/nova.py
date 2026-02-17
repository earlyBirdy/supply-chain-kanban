"""Amazon Nova (Bedrock) connector for hackathon mode.

Goal: make this repo "hackathon-ready" without forcing AWS creds.
- If HACKATHON_MODE=amazon_nova and Bedrock credentials are present, we call Bedrock.
- Otherwise we fall back to a deterministic mock generator that still demonstrates:
  Card -> Recommendation -> Proposed Actions -> (dry_run) validation -> (optional) execute + audit.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class NovaResult:
    ok: bool
    message: str
    recommendation: Dict[str, Any]
    proposed_actions: List[Dict[str, Any]]
    raw: Optional[Dict[str, Any]] = None


def _env(name: str, default: str = "") -> str:
    v = os.getenv(name)
    return v if v is not None else default


def _is_enabled() -> bool:
    return _env("HACKATHON_MODE", "").lower() in {"amazon_nova", "nova", "bedrock_nova"}


def _mock_generate(context: Dict[str, Any], objective: str = "both") -> NovaResult:
    """Deterministic proposal generator (works offline)."""
    card = context.get("card") or {}
    case = context.get("case") or {}
    resource_id = str(case.get("resource_id") or card.get("resource_id") or "unknown")

    risk_score = int(case.get("risk_score") or 70)
    status = str(card.get("status") or "todo")

    # Risk story
    signals = context.get("signals") or {}
    ops = signals.get("ops", [])[:3]
    mkt = signals.get("market", [])[:3]

    highlights = []
    for s in ops:
        highlights.append(f"ops:{s.get('signal_type')}={s.get('value')}")
    for s in mkt:
        highlights.append(f"mkt:{s.get('signal_type')}={s.get('value')}")

    story = (
        f"Resource {resource_id} is at risk (risk_score={risk_score}). "
        f"Current card status={status}. "
        + ("Signals: " + ", ".join(highlights) if highlights else "No recent signals loaded.")
    )

    rec = {
        "title": "Mitigate supply risk with governed actions",
        "summary": story,
        "objective": objective,
        "confidence": float(case.get("confidence") or 0.7),
        "risk_score": risk_score,
    }

    actions: List[Dict[str, Any]] = []

    # 1) Always propose making the card operationally explicit (move to in_progress or blocked).
    if status == "todo":
        actions.append({
            "action_type": "UpdateCardStatus",
            "payload": {
                "card_id": str(card.get("card_id")),
                "new_status": "in_progress",
                "note": "Start mitigation workflow (auto-proposed).",
            },
            "rationale": "Make the risk visible and start the response workflow.",
        })

    # 2) If risk is high, propose blocking with reason (forces SLA + escalation semantics).
    if risk_score >= 80:
        actions.append({
            "action_type": "UpdateCardStatus",
            "payload": {
                "card_id": str(card.get("card_id")),
                "new_status": "blocked",
                "blocked_reason": "High risk detected; awaiting supplier confirmation / contingency capacity.",
            },
            "rationale": "Prevent silent drift; blocking forces explicit resolution path and SLA tracking.",
        })

    # 3) Recommend an external Kinetic action (will go through ERP connector stub).
    actions.append({
        "action_type": "ExpediteShipment",
        "payload": {
            "resource_id": resource_id,
            "priority": "high" if risk_score >= 80 else "normal",
            "reason": "Reduce lead-time risk (auto-proposed).",
        },
        "rationale": "Agent proposes an execution step to reduce lead time exposure.",
    })

    # 4) Optional procurement
    actions.append({
        "action_type": "TriggerPurchase",
        "payload": {
            "resource_id": resource_id,
            "qty": 50,
            "reason": "Buffer stock for at-risk resource (auto-proposed).",
        },
        "rationale": "Increase safety stock to absorb supply volatility.",
    })

    return NovaResult(ok=True, message="ok (mock)", recommendation=rec, proposed_actions=actions, raw=None)


def _bedrock_generate(context: Dict[str, Any], objective: str = "both") -> NovaResult:
    """Best-effort Bedrock invocation. If anything fails, caller should fall back to mock."""
    model_id = _env("NOVA_MODEL_ID", "")
    region = _env("AWS_REGION", _env("AWS_DEFAULT_REGION", "us-east-1"))

    prompt = {
        "task": "supply_chain_risk_mitigation_and_agentic_workflow",
        "objective": objective,
        "requirements": [
            "Return STRICT JSON with keys: recommendation{title,summary,confidence,risk_score}, proposed_actions[list].",
            "Each proposed_actions item must have action_type and payload fields.",
            "Include a short rationale per action.",
            "Prefer UpdateCardStatus + ExpediteShipment + TriggerPurchase if applicable.",
            "Respect governance: blocked requires blocked_reason; resolved requires resolved_at; resolve may require supervisor + high risk.",
        ],
        "context": context,
    }

    # We keep the request format flexible: different Nova variants may expect different keys.
    # We'll try a common 'messages' style first.
    body_candidates = [
        {"messages": [{"role": "user", "content": [{"text": json.dumps(prompt)}]}]},
        {"inputText": json.dumps(prompt)},
        {"prompt": json.dumps(prompt)},
    ]

    try:
        import boto3  # type: ignore
        client = boto3.client("bedrock-runtime", region_name=region)
    except Exception as e:
        return NovaResult(ok=False, message=f"boto3/bedrock client error: {e}", recommendation={}, proposed_actions=[], raw=None)

    last_err = None
    for body in body_candidates:
        try:
            if not model_id:
                return NovaResult(ok=False, message="NOVA_MODEL_ID not set", recommendation={}, proposed_actions=[], raw=None)

            resp = client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body).encode("utf-8"),
            )
            raw_bytes = resp.get("body").read() if hasattr(resp.get("body"), "read") else resp.get("body")
            raw_text = raw_bytes.decode("utf-8") if isinstance(raw_bytes, (bytes, bytearray)) else str(raw_bytes)
            data = json.loads(raw_text)

            # Heuristic: find a JSON payload in common locations
            payload = data
            for k in ["output", "outputs", "result", "content"]:
                if isinstance(payload, dict) and k in payload:
                    payload = payload[k]

            if isinstance(payload, list) and payload and isinstance(payload[0], dict) and "text" in payload[0]:
                # Some models return [{"text": "..."}]
                payload = json.loads(payload[0]["text"])

            if isinstance(payload, dict) and "recommendation" in payload and "proposed_actions" in payload:
                return NovaResult(ok=True, message="ok (bedrock)", recommendation=payload["recommendation"], proposed_actions=payload["proposed_actions"], raw=data)

            # If it returns plain text, attempt extract JSON
            if isinstance(payload, str):
                m = re.search(r"\{.*\}", payload, re.DOTALL)
                if m:
                    parsed = json.loads(m.group(0))
                    if "recommendation" in parsed and "proposed_actions" in parsed:
                        return NovaResult(ok=True, message="ok (bedrock parsed)", recommendation=parsed["recommendation"], proposed_actions=parsed["proposed_actions"], raw=data)

            last_err = f"unexpected response shape: {type(data)}"
        except Exception as e:
            last_err = str(e)

    return NovaResult(ok=False, message=f"bedrock invoke failed: {last_err}", recommendation={}, proposed_actions=[], raw=None)


def generate(context: Dict[str, Any], objective: str = "both") -> NovaResult:
    """Generate a recommendation + proposed actions (Bedrock if enabled, otherwise mock)."""
    if _is_enabled():
        r = _bedrock_generate(context, objective=objective)
        if r.ok:
            return r
        # fall back to mock if bedrock fails
        r2 = _mock_generate(context, objective=objective)
        r2.message = f"{r.message} -> fallback {r2.message}"
        return r2

    return _mock_generate(context, objective=objective)
