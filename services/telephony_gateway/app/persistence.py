from __future__ import annotations

from typing import Any

import httpx


class SessionPersistenceClient:
    """Handles call session lifecycle persistence via the backend API."""

    def __init__(self, base_url: str, *, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def upsert_session(self, session_id: str, attributes: dict[str, Any]) -> None:
        response = await self._client.put(f"/sessions/{session_id}", json={"attributes": attributes})
        response.raise_for_status()

    async def close(self) -> None:
        await self._client.aclose()
