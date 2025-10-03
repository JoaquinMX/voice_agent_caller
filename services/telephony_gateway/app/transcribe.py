from __future__ import annotations

import asyncio
import base64
from typing import Iterable

from amazon_transcribe.client import AmazonTranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

from .config import Settings


class _TranscriptCollector(TranscriptResultStreamHandler):
    def __init__(self, stream) -> None:  # type: ignore[override]
        super().__init__(stream)
        self._segments: list[str] = []

    async def handle_transcript_event(self, transcript_event: TranscriptEvent) -> None:  # type: ignore[override]
        for result in transcript_event.transcript.results:
            if result.is_partial:
                continue
            if result.alternatives:
                self._segments.append(result.alternatives[0].transcript)

    @property
    def transcript(self) -> str:
        return " ".join(self._segments).strip()


class TranscribeStreamingService:
    """Thin wrapper around Amazon Transcribe streaming client."""

    def __init__(self, settings: Settings) -> None:
        self._client = AmazonTranscribeStreamingClient(region=settings.aws_region)
        self._language_code = settings.transcribe_language_code

    async def transcribe_audio(
        self,
        audio_chunks: Iterable[bytes],
        *,
        sample_rate_hz: int,
        encoding: str = "pcm",
    ) -> str:
        stream = await self._client.start_stream_transcription(
            language_code=self._language_code,
            media_sample_rate_hz=sample_rate_hz,
            media_encoding=encoding.upper(),
            enable_partial_results_stabilization=True,
            partial_results_stability="medium",
        )

        async def _write_stream() -> None:
            for chunk in audio_chunks:
                await stream.input_stream.send_audio_event(audio_chunk=chunk)
            await stream.input_stream.end_stream()

        collector = _TranscriptCollector(stream.output_stream)
        await asyncio.gather(_write_stream(), collector.run())
        return collector.transcript

    @staticmethod
    def decode_chunks(payload: Iterable[str]) -> list[bytes]:
        return [base64.b64decode(item) for item in payload]
