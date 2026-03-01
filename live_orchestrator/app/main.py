from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

API_BASE = os.getenv("API_BASE", "http://api:8000").rstrip("/")
WS_DEMO_MODE = os.getenv("WS_DEMO_MODE", "1").strip()  # 1 = deterministic stub

app = FastAPI(title="Gemini Live Orchestrator (Scaffold)", version="0.1")

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
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat(), "api_base": API_BASE, "demo_mode": WS_DEMO_MODE}

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json(
        {
            "type": "hello",
            "message": "Live orchestrator connected (scaffold).",
            "hints": [
                "Send {type:'command', command:'run_memory_burst'} to trigger /demo/run_scenario",
                "Send {type:'command', command:'list_news', topic:'memory'} to fetch /news/items",
            ],
        }
    )

    try:
        while True:
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
            except Exception:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            if data.get("type") != "command":
                await websocket.send_json({"type": "error", "message": "Expected type='command'"})
                continue

            cmd = str(data.get("command") or "").strip()

            if cmd == "run_memory_burst":
                topic = str(data.get("topic") or "memory")
                res = _api_post(
                    "/demo/run_scenario",
                    {"name": "memory_leakage_news_burst", "reset_first": False, "dry_run": False, "risk_score": 86, "memory_topic": topic},
                )
                await websocket.send_json({"type": "scenario_result", "scenario": "memory_leakage_news_burst", "result": res})
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
