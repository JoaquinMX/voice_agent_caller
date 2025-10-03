from __future__ import annotations

from datetime import datetime

from redis.asyncio import Redis

from .schemas import SessionState


class SessionStateStore:
    """Redis-backed storage for conversation state."""

    def __init__(self, client: Redis, ttl_seconds: int) -> None:
        self._client = client
        self._ttl = ttl_seconds

    async def load(self, session_id: str) -> SessionState:
        raw = await self._client.get(self._key(session_id))
        if raw:
            return SessionState.model_validate_json(raw)
        return SessionState(session_id=session_id)

    async def save(self, state: SessionState) -> SessionState:
        state.updated_at = datetime.utcnow()
        await self._client.set(
            self._key(state.session_id),
            state.model_dump_json(),
            ex=self._ttl,
        )
        return state

    async def delete(self, session_id: str) -> None:
        await self._client.delete(self._key(session_id))

    def _key(self, session_id: str) -> str:
        return f"conversation:session:{session_id}"
