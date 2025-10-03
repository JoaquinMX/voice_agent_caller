from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class VoiceResponse(BaseModel):
    """Envelope returned to the telephony provider webhooks."""

    action: str = Field(description="Type of response action for the provider")
    metadata: dict[str, Any] = Field(default_factory=dict)
    response_text: str | None = Field(
        default=None, description="Plain-text response delivered back to the caller"
    )
    audio_base64: str | None = Field(
        default=None,
        description="Base64-encoded audio (mp3) synthesized for playback",
    )
    ssml: str | None = Field(
        default=None, description="SSML used to synthesize the audio response"
    )


class ConversationResult(BaseModel):
    """Shape returned by the conversation orchestrator service."""

    session_id: str
    response_text: str
    ssml: str | None = None
    state: dict[str, Any]
    directives: dict[str, Any] = Field(default_factory=dict)


class StreamRequest(BaseModel):
    """Payload sent by the media gateway to request transcription."""

    call_sid: str = Field(description="Unique call session identifier")
    audio_chunks: list[str] = Field(
        default_factory=list,
        description="List of base64 encoded audio chunks (PCM or Opus)",
    )
    sample_rate_hz: int = Field(default=8000, description="Sample rate of the input audio")
    encoding: str = Field(default="pcm", description="Encoding of the audio stream")
    locale: str | None = Field(default=None, description="Locale hint for transcription")
    metadata: dict[str, Any] = Field(default_factory=dict)
