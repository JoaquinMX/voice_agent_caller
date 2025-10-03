from __future__ import annotations

from typing import Any

import httpx


class ConversationClient:
    """Thin wrapper around the conversation orchestrator HTTP API."""

    def __init__(self, base_url: str, *, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def advance(self, session_id: str, user_input: str, locale: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"session_id": session_id, "user_input": user_input}
        if locale:
            payload["locale"] = locale
        response = await self._client.post("/conversation", json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
