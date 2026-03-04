from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

import requests
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

from .gemini_live import GeminiLiveBridge, safe_close
from .tools_backend import (
    build_grounded_context,
    build_structured_citations,
    classify_tools_for_prompt,
    run_tools,
)

API_BASE = os.getenv("API_BASE", "http://api:8000").rstrip("/")
ORCHESTRATOR_MODE = os.getenv("ORCHESTRATOR_MODE", "scaffold").strip().lower()
# scaffold: deterministic websocket bridge (Devpost-friendly)
# gemini_live: connects to Gemini Live API (keep deterministic commands available)

app = FastAPI(title="Gemini Live Orchestrator", version="0.2")


def _api_post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{API_BASE}{path}"
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def _api_get(path: str) -> Dict[str, Any]:
    url = f"{API_BASE}{path}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


@app.get("/healthz")
def healthz():
    return {
        "ok": True,
        "ts": datetime.now(timezone.utc).isoformat(),
        "api_base": API_BASE,
        "mode": ORCHESTRATOR_MODE,
    }


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()

    await websocket.send_json(
        {
            "type": "hello",
            "message": f"Live orchestrator connected ({ORCHESTRATOR_MODE}).",
            "hints": [
                "Commands are deterministic: run_memory_burst / list_news / list_alerts",
                "Optional (gemini_live mode): send {type:'text', text:'...'} for Gemini Live response",
            ],
        }
    )

    live_bridge: GeminiLiveBridge | None = None
    live_session: Any | None = None
    if ORCHESTRATOR_MODE == "gemini_live":
        try:
            live_bridge = GeminiLiveBridge()
            live_session = await live_bridge.connect()
            await websocket.send_json(
                {"type": "gemini_live", "status": "connected", "model": live_bridge.model}
            )
        except Exception as e:
            await websocket.send_json(
                {"type": "gemini_live", "status": "disabled", "error": str(e)}
            )
            live_bridge = None
            live_session = None

    try:
        while True:
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
            except Exception:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            mtype = str(data.get("type") or "").strip()

            # Gemini Live text turn (optional)
            if mtype in ("text", "user_message"):
                if not (live_bridge and live_session):
                    await websocket.send_json(
                        {
                            "type": "gemini_live",
                            "status": "not_connected",
                            "message": "Set ORCHESTRATOR_MODE=gemini_live and provide credentials.",
                        }
                    )
                    continue
                text = str(data.get("text") or "").strip()
                if not text:
                    await websocket.send_json({"type": "error", "message": "Missing text"})
                    continue

                # Tool-backed grounding: fetch latest alerts/news/cases when the prompt suggests it.
                tool_plan = classify_tools_for_prompt(text)
                tool_results = run_tools(tool_plan) if tool_plan else {"tools": []}

                citations = None
                if tool_results.get("tools"):
                    citations = build_structured_citations(tool_results)

                # Surface tool calls/results to the UI for transparency.
                if tool_results.get("tools"):
                    await websocket.send_json({"type": "tool_results", "for": "user_prompt", "plan": tool_plan, "results": tool_results})

                # Send a compact, cited evidence block the UI can render nicely.
                if citations and (citations.get("alerts") or citations.get("news") or citations.get("cases")):
                    await websocket.send_json({"type": "grounded_summary", "summary": citations})

                grounded_prompt = text
                if tool_results.get("tools"):
                    cited_block = citations.get("bullets_markdown") if citations else ""
                    grounded_prompt = (
                        build_grounded_context(tool_results)
                        + "\n\nCitations (use bracket labels like [A1], [N2] in your answer):\n"
                        + (cited_block or "(no citations)")
                        + "\n\nUser: "
                        + text
                    )

                try:
                    resp = await live_bridge.ask_text(live_session, grounded_prompt)
                    await websocket.send_json({"type": "gemini_text", "text": resp})
                except Exception as e:
                    await websocket.send_json({"type": "error", "message": f"Gemini Live error: {e}"})
                continue

            # Deterministic commands (works in both modes)
            if mtype != "command":
                await websocket.send_json({"type": "error", "message": "Expected type='command' or type='text'"})
                continue

            cmd = str(data.get("command") or "").strip()

            if cmd == "run_memory_burst":
                topic = str(data.get("topic") or "memory")
                res = _api_post(
                    "/demo/run_scenario",
                    {
                        "name": "memory_leakage_news_burst",
                        "reset_first": False,
                        "dry_run": False,
                        "risk_score": 86,
                        "memory_topic": topic,
                    },
                )
                await websocket.send_json(
                    {"type": "scenario_result", "scenario": "memory_leakage_news_burst", "result": res}
                )
                continue

            if cmd == "list_news":
                topic = data.get("topic")
                if topic:
                    res = _api_get(f"/news/items?topic={topic}&limit=50")
                else:
                    res = _api_get("/news/items?limit=50")
                await websocket.send_json({"type": "news_items", "topic": topic, "result": res})
                continue

            if cmd == "list_alerts":
                topic = data.get("topic")
                if topic:
                    res = _api_get(f"/news/alerts?topic={topic}&limit=50")
                else:
                    res = _api_get("/news/alerts?limit=50")
                await websocket.send_json({"type": "news_alerts", "topic": topic, "result": res})
                continue

            await websocket.send_json({"type": "error", "message": f"Unknown command: {cmd}"})

    except WebSocketDisconnect:
        return
    finally:
        if live_session is not None:
            await safe_close(live_session)
