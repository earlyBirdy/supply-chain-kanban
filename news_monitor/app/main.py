from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("API_BASE", "http://api:8000").rstrip("/")
TOPIC = os.getenv("NEWS_TOPIC", "memory")
MODE = os.getenv("NEWS_MODE", "sample_once")  # sample_once | loop
INTERVAL_SECONDS = int(os.getenv("NEWS_INTERVAL_SECONDS", "900"))

def post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{API_BASE}{path}"
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def run_sample_once() -> None:
    # Reuse API's DEV_MODE helper for a deterministic, demo-safe burst.
    res = requests.post(f"{API_BASE}/news/check-now?topic={TOPIC}", timeout=30)
    res.raise_for_status()
    print(res.json(), flush=True)

def main() -> None:
    print(f"[news_monitor] mode={MODE} api={API_BASE} topic={TOPIC}", flush=True)

    if MODE == "sample_once":
        run_sample_once()
        return

    if MODE == "loop":
        while True:
            try:
                run_sample_once()
            except Exception as e:
                print(f"[news_monitor] error: {e}", flush=True)
            time.sleep(INTERVAL_SECONDS)
        return

    raise SystemExit(f"Unknown NEWS_MODE: {MODE}")

if __name__ == "__main__":
    main()
