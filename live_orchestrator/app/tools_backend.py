from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple, Optional

import requests

API_BASE = os.getenv("API_BASE", "http://api:8000").rstrip("/")
REQUEST_TIMEOUT = float(os.getenv("TOOL_TIMEOUT_SECONDS", "20"))

def api_get_json(path: str) -> Dict[str, Any]:
    url = f"{API_BASE}{path}"
    r = requests.get(url, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()

def _clip(obj: Any, max_chars: int = 6000) -> Any:
    # Avoid flooding Live API turns.
    s = str(obj)
    if len(s) <= max_chars:
        return obj
    return s[:max_chars] + "...(clipped)"

def fetch_news_items(topic: str = "memory", limit: int = 20) -> Dict[str, Any]:
    return api_get_json(f"/news/items?topic={topic}&limit={limit}")

def fetch_news_alerts(topic: str = "memory", limit: int = 10) -> Dict[str, Any]:
    return api_get_json(f"/news/alerts?topic={topic}&limit={limit}")

def fetch_cases(limit: int = 10) -> Dict[str, Any]:
    # Cases router is mounted at /cases
    return api_get_json(f"/cases?limit={limit}")

def classify_tools_for_prompt(prompt: str) -> List[Tuple[str, Dict[str, Any]]]:
    p = prompt.lower().strip()
    tools: List[Tuple[str, Dict[str, Any]]] = []

    # Very small intent rules to keep demo deterministic and reliable.
    if any(k in p for k in ["latest", "recent", "what's new", "update", "signal", "leakage", "oversupply", "price", "inventory"]):
        tools.append(("news_alerts", {"topic": "memory", "limit": 10}))
        tools.append(("news_items", {"topic": "memory", "limit": 25}))

    if any(k in p for k in ["case", "cases", "kanban", "incident", "open case", "status"]):
        tools.append(("cases", {"limit": 10}))

    # If user explicitly mentions DRAM or NAND/flash, bias to memory topic already.
    # (Future: parse topic keywords into topic selection.)
    return tools

def run_tools(tool_plan: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"tools": []}
    for name, args in tool_plan:
        try:
            if name == "news_items":
                data = fetch_news_items(**args)
            elif name == "news_alerts":
                data = fetch_news_alerts(**args)
            elif name == "cases":
                data = fetch_cases(**args)
            else:
                data = {"error": f"unknown tool {name}"}
            out["tools"].append({"name": name, "args": args, "ok": True, "data": _clip(data)})
        except Exception as e:
            out["tools"].append({"name": name, "args": args, "ok": False, "error": str(e)})
    return out

def build_grounded_context(tool_results: Dict[str, Any]) -> str:
    """System-style instruction block for grounded answers.

    The caller may append a citations block. This function enforces a strict,
    judge-friendly response template and prohibits invention.
    """
    return (
        "You are a supply-chain risk agent for AI data centers.\n"
        "\n"
        "GROUNDING RULES (mandatory):\n"
        "- Use ONLY the tool results and the provided citation items as facts.\n"
        "- Every factual claim MUST cite at least one bracket label like [A1] or [N2] or [C1].\n"
        "- If the tool results are insufficient, say exactly what is missing and what tool you would call next.\n"
        "- Do NOT invent numbers, dates, vendors, or causes.\n"
        "\n"
        "OUTPUT FORMAT (mandatory, Markdown, use this exact template):\n"
        "### Top alert\n"
        "- <1–2 sentences summarizing the single most important alert or say 'No alerts found'> [A#] [N#]\n"
        "\n"
        "### Top 3 evidence\n"
        "1. <evidence bullet, include vendor/product + what changed + timeframe> [N#]\n"
        "2. <evidence bullet> [N#]\n"
        "3. <evidence bullet> [N#]\n"
        "\n"
        "### Recommended next action\n"
        "- <one concrete action you recommend, prefer existing case/action if present> [C#] [A#]\n"
        "\n"
        "### Confidence\n"
        "- <High/Medium/Low> — <why, based on source diversity/recency/consistency> [A#] [N#]\n"
        "\n"
        "Tool results (JSON):\n"
        f"{tool_results}"
    )

def _as_list(payload: Any) -> List[Dict[str, Any]]:
    """Best-effort: normalize API payloads into a list of dict records."""
    if payload is None:
        return []
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for k in ("items", "alerts", "news", "results", "data"):
            v = payload.get(k)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
        if "id" in payload or "title" in payload:
            return [payload]
    return []


def _pick_str(d: Dict[str, Any], keys: List[str]) -> Optional[str]:
    for k in keys:
        v = d.get(k)
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return None


def _pick_float(d: Dict[str, Any], keys: List[str]) -> Optional[float]:
    for k in keys:
        v = d.get(k)
        if v is None:
            continue
        try:
            return float(v)
        except Exception:
            continue
    return None


def build_structured_citations(tool_results: Dict[str, Any], max_each: int = 5) -> Dict[str, Any]:
    """Create a compact, cited evidence block for UI + for prompting the model."""
    alerts: List[Dict[str, Any]] = []
    news: List[Dict[str, Any]] = []
    cases: List[Dict[str, Any]] = []

    tools = tool_results.get("tools") or []
    for t in tools:
        if not isinstance(t, dict) or not t.get("ok"):
            continue
        name = t.get("name")
        data = t.get("data")
        records = _as_list(data)
        if name == "news_alerts":
            for r in records[:max_each]:
                title = _pick_str(r, ["title", "headline", "summary", "reason"]) or "(untitled alert)"
                ts = _pick_str(r, ["ts", "created_at", "published_at", "published", "time"]) or ""
                score = _pick_float(r, ["score", "severity", "risk_score"])
                url = _pick_str(r, ["url", "source_url", "link"]) or ""
                alerts.append({"title": title, "ts": ts, "score": score, "url": url})
        elif name == "news_items":
            for r in records[:max_each]:
                title = _pick_str(r, ["title", "headline", "summary"]) or "(untitled news)"
                ts = _pick_str(r, ["ts", "published_at", "published", "created_at", "time"]) or ""
                score = _pick_float(r, ["score", "severity"])
                url = _pick_str(r, ["url", "source_url", "link"]) or ""
                news.append({"title": title, "ts": ts, "score": score, "url": url})
        elif name == "cases":
            for r in records[:max_each]:
                title = _pick_str(r, ["title", "name", "case_title"]) or "(untitled case)"
                ts = _pick_str(r, ["created_at", "ts", "updated_at"]) or ""
                score = _pick_float(r, ["risk_score", "score", "severity"])
                url = _pick_str(r, ["url"]) or ""
                cases.append({"title": title, "ts": ts, "score": score, "url": url})

    def labelize(prefix: str, arr: List[Dict[str, Any]]):
        for i, r in enumerate(arr, start=1):
            r["label"] = f"{prefix}{i}"

    labelize("A", alerts)
    labelize("N", news)
    labelize("C", cases)

    lines: List[str] = []
    for r in alerts:
        score_txt = f" score={r['score']:.0f}" if isinstance(r.get("score"), (int, float)) else ""
        url = r.get("url") or ""
        lines.append(f"- [{r['label']}] {r['title']} ({r.get('ts','')}{score_txt}) {url}".strip())
    for r in news:
        score_txt = f" score={r['score']:.0f}" if isinstance(r.get("score"), (int, float)) else ""
        url = r.get("url") or ""
        lines.append(f"- [{r['label']}] {r['title']} ({r.get('ts','')}{score_txt}) {url}".strip())
    for r in cases:
        score_txt = f" score={r['score']:.0f}" if isinstance(r.get("score"), (int, float)) else ""
        url = r.get("url") or ""
        lines.append(f"- [{r['label']}] {r['title']} ({r.get('ts','')}{score_txt}) {url}".strip())

    return {
        "alerts": alerts,
        "news": news,
        "cases": cases,
        "bullets_markdown": "\n".join(lines).strip(),
    }
