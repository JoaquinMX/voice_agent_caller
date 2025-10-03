from __future__ import annotations

from typing import Sequence

from openai import AsyncOpenAI


class LLMClient:
    """Wrapper around OpenAI responses API with graceful fallback."""

    def __init__(self, api_key: str | None) -> None:
        self._api_key = api_key
        self._client = AsyncOpenAI(api_key=api_key) if api_key else None

    async def generate_response(self, messages: Sequence[dict[str, str]]) -> str:
        if self._client is None:
            return "Gracias por la información. Procederé con los siguientes pasos y te mantendré al tanto."

        completion = await self._client.responses.create(
            model="gpt-4o-mini",
            input=messages,
            temperature=0.3,
        )
        return completion.output_text or "Entendido, continuaré ayudándote con gusto."
