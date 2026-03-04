from __future__ import annotations

import asyncio
import os
from typing import Any, AsyncIterator, Dict, Optional

# Optional dependency: only required when ORCHESTRATOR_MODE=gemini_live.
# Install: pip install google-genai
try:
    from google import genai
    from google.genai import types
except Exception as e:  # pragma: no cover
    genai = None  # type: ignore
    types = None  # type: ignore
    _IMPORT_ERR = e
else:
    _IMPORT_ERR = None


class GeminiLiveBridge:
    """Tiny wrapper around the Google Gen AI SDK Live API.

    This keeps our web demo + deterministic orchestration intact, while allowing a
    real Gemini Live session to be used for conversational commands.
    """

    def __init__(self) -> None:
        if genai is None:  # pragma: no cover
            raise RuntimeError(
                "google-genai is not installed or failed to import. "
                "Install it in live_orchestrator (pip install google-genai). "
                f"Import error: {_IMPORT_ERR}"
            )

        # Supports both Gemini Developer API (API key) and Vertex AI (ADC).
        # - Gemini Developer API: set GEMINI_API_KEY or GOOGLE_API_KEY
        # - Vertex AI: set GOOGLE_GENAI_USE_VERTEXAI=true, GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION
        self.client = genai.Client().aio
        self.model = os.getenv("GEMINI_LIVE_MODEL", "gemini-live-2.5-flash-native-audio").strip()

    async def connect(self) -> Any:
        # Minimal config: text-in/text-out.
        # The Live API is WebSocket-based; use an async session.
        config = types.LiveConnectConfig(
            response_modalities=["TEXT"],
        )
        return await self.client.live.connect(model=self.model, config=config)

    async def ask_text(self, session: Any, text: str) -> str:
        # Send a single text turn and collect text output.
        # Per Live API docs: session.send_client_content(turns=message, turn_complete=True)
        await session.send_client_content(turns=text, turn_complete=True)

        chunks: list[str] = []
        async for ev in session.receive():
            # SDK yields a variety of event objects; we try to extract text parts robustly.
            try:
                etype = getattr(ev, "type", None) or getattr(ev, "event_type", None)
                if etype == "content":
                    content = getattr(ev, "content", None)
                    parts = None
                    if isinstance(content, dict):
                        parts = content.get("parts")
                    else:
                        parts = getattr(content, "parts", None)
                    if parts:
                        for p in parts:
                            if isinstance(p, dict):
                                t = p.get("text")
                            else:
                                t = getattr(p, "text", None)
                            if t:
                                chunks.append(str(t))
                if etype in ("turn_complete", "response_complete"):
                    break
            except Exception:
                continue

        return "".join(chunks).strip()


async def safe_close(session: Any) -> None:
    try:
        await session.aclose()
    except Exception:
        try:
            await session.close()
        except Exception:
            return
