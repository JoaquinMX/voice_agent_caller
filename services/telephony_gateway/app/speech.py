from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from redis.asyncio import Redis

from .config import Settings


@dataclass
class SynthesizedAudio:
    """Container for synthesized speech ready for playback."""

    ssml: str
    audio_base64: str
    format: str
    voice_id: str


class SpeechCache:
    """Redis-backed cache to avoid re-synthesizing repeated prompts."""

    def __init__(self, client: Redis, ttl_seconds: int) -> None:
        self._client = client
        self._ttl = ttl_seconds

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set(self, key: str, value: str) -> None:
        await self._client.set(key, value, ex=self._ttl)


class PollySynthesizer:
    """Wraps Amazon Polly neural voices."""

    def __init__(self, settings: Settings) -> None:
        self._client = boto3.client("polly", region_name=settings.aws_region)
        self._voice_id = settings.polly_voice_id
        self._engine = settings.polly_engine
        self._language = settings.transcribe_language_code

    def synthesize(self, text_or_ssml: str, is_ssml: bool = True) -> bytes:
        try:
            response = self._client.synthesize_speech(
                Text=text_or_ssml,
                TextType="ssml" if is_ssml else "text",
                OutputFormat="mp3",
                VoiceId=self._voice_id,
                Engine=self._engine,
                LanguageCode=self._language,
            )
        except (BotoCoreError, ClientError) as exc:  # pragma: no cover - network failure path
            raise RuntimeError("Failed to synthesize speech with Amazon Polly") from exc

        audio_stream = response.get("AudioStream")
        if audio_stream is None:  # pragma: no cover - safety check
            raise RuntimeError("Amazon Polly did not return an audio stream")
        return audio_stream.read()


class SpeechPipeline:
    """Coordinates caching and synthesis for Spanish agent responses."""

    def __init__(self, settings: Settings, redis_client: Redis) -> None:
        self._settings = settings
        self._cache = SpeechCache(redis_client, settings.audio_cache_ttl_seconds)
        self._synthesizer = PollySynthesizer(settings)

    async def synthesize(self, response_text: str, *, speaking_style: str | None = None) -> SynthesizedAudio:
        ssml = self._to_ssml(response_text, speaking_style=speaking_style)
        cache_key = self._cache_key(ssml)

        cached_audio = await self._cache.get(cache_key)
        if cached_audio:
            return SynthesizedAudio(
                ssml=ssml,
                audio_base64=cached_audio,
                format="mp3",
                voice_id=self._settings.polly_voice_id,
            )

        audio_bytes = self._synthesizer.synthesize(ssml, is_ssml=True)
        encoded = base64.b64encode(audio_bytes).decode()
        await self._cache.set(cache_key, encoded)
        return SynthesizedAudio(
            ssml=ssml,
            audio_base64=encoded,
            format="mp3",
            voice_id=self._settings.polly_voice_id,
        )

    @staticmethod
    def _cache_key(ssml: str) -> str:
        digest = hashlib.sha1(ssml.encode("utf-8")).hexdigest()
        return f"polly:ssml:{digest}"

    @staticmethod
    def _to_ssml(text: str, *, speaking_style: str | None = None) -> str:
        style = speaking_style or "conversational"
        return (
            "<speak>"
            f"<amazon:domain name=\"{style}\">{text}</amazon:domain>"
            "</speak>"
        )
