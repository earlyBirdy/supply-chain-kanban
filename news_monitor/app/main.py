from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import requests
from dotenv import load_dotenv

# Optional dependency for NEWS_MODE=rss
try:
    import feedparser  # type: ignore
except Exception:
    feedparser = None  # type: ignore

load_dotenv()

API_BASE = os.getenv("API_BASE", "http://api:8000").rstrip("/")
TOPIC = os.getenv("NEWS_TOPIC", "memory").strip()
NEWS_MODE = os.getenv("NEWS_MODE", "deterministic").strip().lower()
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "30"))
DEV_MODE = os.getenv("DEV_MODE", "1").strip()  # allow /news/check-now in dev

RSS_ALLOWLIST_PATH = os.getenv("RSS_ALLOWLIST_PATH", "/app/app/rss_sources.yaml")


@dataclass
class RssSource:
    name: str
    url: str
    weight: float = 1.0


def _api_post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.post(f"{API_BASE}{path}", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def _api_get(path: str) -> Dict[str, Any]:
    r = requests.get(f"{API_BASE}{path}", timeout=30)
    r.raise_for_status()
    return r.json()


def load_rss_sources() -> List[RssSource]:
    # Tiny YAML-ish parser (keeps deps minimal). Format is fixed in rss_sources.yaml.
    # If you prefer full YAML: add PyYAML and parse properly.
    txt = ""
    try:
        with open(RSS_ALLOWLIST_PATH, "r", encoding="utf-8") as f:
            txt = f.read()
    except FileNotFoundError:
        return []

    sources: List[RssSource] = []
    cur: Dict[str, Any] = {}
    for raw in txt.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            if cur:
                sources.append(RssSource(**cur))  # type: ignore[arg-type]
            cur = {}
            line = line[2:].strip()
            if line.startswith("name:"):
                cur["name"] = line.split(":", 1)[1].strip().strip('"')
        elif ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"')
            if k == "weight":
                try:
                    cur[k] = float(v)
                except Exception:
                    cur[k] = 1.0
            else:
                cur[k] = v
    if cur:
        sources.append(RssSource(**cur))  # type: ignore[arg-type]
    return sources


KEYWORDS = [
    ("leak", 30),
    ("leakage", 30),
    ("dump", 25),
    ("inventory", 20),
    ("oversupply", 20),
    ("shortage", 18),
    ("price", 15),
    ("spot", 10),
    ("contract", 10),
    ("HBM", 12),
    ("DRAM", 12),
    ("NAND", 12),
    ("flash", 8),
    ("datacenter", 10),
    ("data center", 10),
    ("AI", 6),
]


def score_item(title: str, summary: str, base: float) -> int:
    s = (title + " " + summary).lower()
    score = int(30 + 50 * base)
    for kw, pts in KEYWORDS:
        if kw.lower() in s:
            score += pts
    return max(0, min(100, score))


def fetch_rss_items() -> List[Dict[str, Any]]:
    if feedparser is None:
        raise RuntimeError("feedparser not installed (pip install feedparser)")

    sources = load_rss_sources()
    items: List[Dict[str, Any]] = []
    for src in sources:
        feed = feedparser.parse(src.url)  # type: ignore[attr-defined]
        for e in feed.entries[:20]:
            title = getattr(e, "title", "") or ""
            link = getattr(e, "link", "") or ""
            summary = getattr(e, "summary", "") or ""
            score = score_item(title, summary, src.weight)
            if not link or not title:
                continue
            items.append(
                {
                    "topic": TOPIC,
                    "title": title,
                    "url": link,
                    "source": src.name,
                    "score": score,
                    "summary": summary[:4000],
                }
            )
    return items


def ingest_items(items: List[Dict[str, Any]]) -> Tuple[int, int]:
    if not items:
        return (0, 0)
    res = _api_post("/news/ingest", {"items": items})
    return int(res.get("inserted", 0)), int(res.get("deduped", 0))


def run_once() -> Dict[str, Any]:
    if NEWS_MODE == "deterministic":
        # Devpost-friendly: deterministic burst is triggered by /demo/run_scenario
        return {"mode": NEWS_MODE, "hint": "Use /demo/run_scenario to simulate a burst."}

    if NEWS_MODE == "rss":
        rss_items = fetch_rss_items()
        inserted, deduped = ingest_items(rss_items)
        return {"mode": NEWS_MODE, "fetched": len(rss_items), "inserted": inserted, "deduped": deduped}

    if NEWS_MODE == "check_now":
        # Legacy dev-mode hook (kept for convenience).
        if DEV_MODE != "1":
            return {"mode": NEWS_MODE, "disabled": True}
        return _api_post("/news/check-now", {"topic": TOPIC})

    return {"mode": NEWS_MODE, "error": "unknown NEWS_MODE"}


def main() -> None:
    print(json.dumps({"service": "news_monitor", "api_base": API_BASE, "topic": TOPIC, "mode": NEWS_MODE}))
    while True:
        try:
            out = run_once()
            print(json.dumps(out))
        except Exception as e:
            print(json.dumps({"error": str(e), "mode": NEWS_MODE}))
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
