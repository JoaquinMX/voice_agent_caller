from __future__ import annotations

import json
from dataclasses import dataclass

from redis.asyncio import Redis


@dataclass
class RedisEventBus:
    """Publish-only event bus backed by Redis channels."""

    client: Redis
    channel_prefix: str = "telephony"

    async def publish(self, topic: str, payload: dict) -> None:
        channel = f"{self.channel_prefix}:{topic}"
        message = json.dumps(payload, default=str)
        await self.client.publish(channel, message)
