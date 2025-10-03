from __future__ import annotations

from typing import Any

import httpx


class TranscriptLogger:
    """Persists session metadata and transcript segments via the backend API."""

    def __init__(self, base_url: str, *, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def ensure_session(self, session_id: str, attributes: dict[str, Any]) -> None:
        response = await self._client.put(f"/sessions/{session_id}", json={"attributes": attributes})
        response.raise_for_status()

    async def append_segment(
        self,
        session_id: str,
        *,
        role: str,
        content: str,
        sequence: int,
        locale: str,
    ) -> None:
        payload = {
            "role": role,
            "content": content,
            "sequence": sequence,
            "locale": locale,
        }
        response = await self._client.post(
            f"/sessions/{session_id}/transcripts",
            json=payload,
        )
        response.raise_for_status()

    async def close(self) -> None:
        await self._client.aclose()
