"""Streamlit AI-agent debug cockpit for Supply Chain Kanban AI Agent.

This app is intentionally read-mostly. It calls the FastAPI surface instead of
reaching into private DB tables, so it debugs the same contracts the operator UI
uses.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import streamlit as st

DEFAULT_API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


st.set_page_config(
    page_title="Supply Chain AI Agent Debug Cockpit",
    page_icon="🧭",
    layout="wide",
)


@st.cache_data(ttl=10)
def api_get(path: str) -> Any:
    url = f"{DEFAULT_API_BASE}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Cannot reach API at {url}: {exc.reason}") from exc


def safe_get(path: str, fallback: Any) -> Any:
    try:
        return api_get(path)
    except Exception as exc:  # Streamlit should show useful debug state.
        st.error(str(exc))
        return fallback


def render_json(label: str, data: Any) -> None:
    with st.expander(label, expanded=False):
        st.json(data)


st.title("Supply Chain AI Agent Debug Cockpit")
st.caption(
    "Read-mostly Streamlit cockpit for agent traces, Kanban risk cases, "
    "SiteTrack evidence, ERP writeback receipts, and blockchain proof status."
)

with st.sidebar:
    st.header("Connection")
    st.code(DEFAULT_API_BASE)
    st.caption("Override with API_BASE_URL=http://localhost:8000")
    if st.button("Clear cache / refresh"):
        st.cache_data.clear()
        st.rerun()

health = safe_get("/healthz", {})
ready = safe_get("/readyz", {})
col_a, col_b, col_c = st.columns(3)
col_a.metric("API health", "ok" if health else "offline")
col_b.metric("Readiness", "ready" if ready else "unknown")
col_c.metric("Mode", os.getenv("APP_ENV", "local/debug"))

cases = safe_get("/cases?limit=100", [])
if not isinstance(cases, list):
    cases = []

st.subheader("Kanban Risk Cases")
if cases:
    case_rows = [
        {
            "case_id": c.get("case_id"),
            "status": c.get("status"),
            "risk_score": c.get("risk_score"),
            "title": c.get("title") or c.get("summary") or c.get("case_id"),
            "resource_id": c.get("resource_id"),
            "updated_at": c.get("updated_at"),
        }
        for c in cases
    ]
    st.dataframe(case_rows, use_container_width=True, hide_index=True)
else:
    st.info("No cases returned. Start the demo with `make demo-web` and seed data if needed.")

case_options = [str(c.get("case_id")) for c in cases if c.get("case_id")]
selected_case = st.selectbox("Inspect case", case_options, index=0 if case_options else None)

if selected_case:
    left, right = st.columns([1, 1])
    case = safe_get(f"/cases/{urllib.parse.quote(selected_case)}", {})
    recs = safe_get(f"/cases/{urllib.parse.quote(selected_case)}/recommendations", {})
    actions = safe_get(f"/cases/{urllib.parse.quote(selected_case)}/actions", {})
    audit = safe_get(f"/audit/by_case/{urllib.parse.quote(selected_case)}", {})

    with left:
        st.subheader("Manager-Agent Case Brief")
        st.write(case.get("title") or case.get("summary") or selected_case)
        st.write("**Status:**", case.get("status", "unknown"))
        st.write("**Risk score:**", case.get("risk_score", "unknown"))
        st.write("**Resource:**", case.get("resource_id", "unknown"))
        render_json("Raw case payload", case)

        st.subheader("AI Recommendations")
        recommendations = recs.get("recommendations", []) if isinstance(recs, dict) else []
        if recommendations:
            st.dataframe(recommendations, use_container_width=True, hide_index=True)
        else:
            st.info("No recommendations found for this case.")
        render_json("Raw recommendations", recs)

    with right:
        st.subheader("Execution Receipts / Actions")
        action_items = actions.get("actions", []) if isinstance(actions, dict) else []
        if action_items:
            st.dataframe(action_items, use_container_width=True, hide_index=True)
        else:
            st.info("No actions or receipts found for this case.")
        render_json("Raw actions", actions)

        st.subheader("Audit Timeline")
        audit_items = audit.get("items", []) if isinstance(audit, dict) else []
        if audit_items:
            st.dataframe(audit_items, use_container_width=True, hide_index=True)
        else:
            st.info("No audit events found for this case.")
        render_json("Raw audit", audit)

st.subheader("Evidence Layers to Add Next")
st.markdown(
    """
- **SiteTrack container evidence:** signed last-seen, geofence, handoff, and offline capture payloads.
- **ERP/WMS/TMS receipts:** writeback result, external document id, retry/idempotency status.
- **Blockchain proof status:** proof hash, ledger transaction id, anchor status, correction event pointer.
- **Agent trace:** input signals, reasoning summary, policy decision, and manager-ready recommendation.
"""
)
