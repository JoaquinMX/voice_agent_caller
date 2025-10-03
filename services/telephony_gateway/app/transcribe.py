from __future__ import annotations

import asyncio
import base64
from typing import Iterable

import boto3

from .config import Settings


class TranscribeStreamingService:
    """Thin wrapper around Amazon Transcribe streaming client using boto3."""

    def __init__(self, settings: Settings) -> None:
        self._client = boto3.client('transcribe', region_name=settings.aws_region)
        self._language_code = settings.transcribe_language_code

    async def transcribe_audio(
        self,
        audio_chunks: Iterable[bytes],
        *,
        sample_rate_hz: int,
        encoding: str = "pcm",
    ) -> str:
        # Start the stream
        stream = self._client.start_stream_transcription(
            language_code=self._language_code,
            media_sample_rate_hz=sample_rate_hz,
            media_encoding=encoding.upper(),
            enable_partial_results_stabilization=True,
            partial_results_stability="medium",
        )

        # Collect transcripts
        transcripts = []

        async def send_audio():
            for chunk in audio_chunks:
                await stream.input_stream.send_audio_event(audio_chunk=chunk)
            await stream.input_stream.end_stream()

        async def receive_transcripts():
            async for event in stream.output_stream:
                if 'Transcript' in event:
                    results = event['Transcript']['Results']
                    for result in results:
                        if not result.get('IsPartial', False):
                            alternatives = result.get('Alternatives', [])
                            if alternatives:
                                transcripts.append(alternatives[0]['Transcript'])

        await asyncio.gather(send_audio(), receive_transcripts())

        return " ".join(transcripts).strip()

    @staticmethod
    def decode_chunks(payload: Iterable[str]) -> list[bytes]:
        return [base64.b64decode(item) for item in payload]
