from __future__ import annotations

import logging
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
import redis.asyncio as redis

from .config import Settings, get_settings
from .conversation import ConversationClient
from .events import RedisEventBus
from .persistence import SessionPersistenceClient
from .schemas import ConversationResult, StreamRequest, VoiceResponse
from .speech import SpeechPipeline
from .transcribe import TranscribeStreamingService

logger = logging.getLogger(__name__)

app = FastAPI(title="Telephony Gateway", version="0.2.0")


async def _parse_twilio_payload(request: Request) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        return await request.json()
    form = await request.form()
    return {key: value for key, value in form.multi_items()}


def _resolve_locale(payload: dict[str, Any], settings: Settings) -> str:
    return payload.get("Language") or payload.get("locale") or settings.transcribe_language_code


@app.on_event("startup")
async def startup_event() -> None:
    settings = get_settings()
    app.state.settings = settings
    app.state.redis = redis.from_url(settings.redis_url, decode_responses=True)
    app.state.event_bus = RedisEventBus(app.state.redis)
    app.state.conversation = ConversationClient(str(settings.orchestrator_url))
    app.state.persistence = SessionPersistenceClient(str(settings.backend_api_url))
    app.state.speech_pipeline = SpeechPipeline(settings, app.state.redis)
    app.state.transcribe = TranscribeStreamingService(settings)
    logger.info("Telephony gateway started with region %s", settings.aws_region)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await app.state.conversation.close()
    await app.state.persistence.close()
    await app.state.redis.close()
    await app.state.redis.wait_closed()


@app.post("/twilio/webhook/voice", response_model=VoiceResponse)
async def handle_twilio_voice(
    request: Request, background_tasks: BackgroundTasks
) -> VoiceResponse:
    payload = await _parse_twilio_payload(request)
    call_sid = payload.get("CallSid") or payload.get("call_sid")
    if not call_sid:
        raise HTTPException(status_code=400, detail="Missing CallSid from payload")

    background_tasks.add_task(app.state.event_bus.publish, "call.events", payload)
    await app.state.persistence.upsert_session(
        call_sid, {"provider_payload": payload, "locale": _resolve_locale(payload, app.state.settings)}
    )

    speech_result = payload.get("SpeechResult") or payload.get("speech_result")
    if speech_result:
        locale = _resolve_locale(payload, app.state.settings)
        orchestrator_raw = await app.state.conversation.advance(call_sid, speech_result, locale=locale)
        orchestrator = ConversationResult.model_validate(orchestrator_raw)
        audio = await app.state.speech_pipeline.synthesize(
            orchestrator.response_text,
            speaking_style=orchestrator.directives.get("speaking_style"),
        )
        return VoiceResponse(
            action="play_audio",
            metadata={"provider": "twilio", "call_sid": call_sid},
            response_text=orchestrator.response_text,
            audio_base64=audio.audio_base64,
            ssml=audio.ssml,
        )

    return VoiceResponse(
        action="ack",
        metadata={"provider": "twilio", "call_sid": call_sid},
    )


@app.post("/twilio/webhook/status", response_model=VoiceResponse)
async def handle_twilio_status(request: Request, background_tasks: BackgroundTasks) -> VoiceResponse:
    payload = await _parse_twilio_payload(request)
    background_tasks.add_task(app.state.event_bus.publish, "call.status", payload)
    call_sid = payload.get("CallSid") or payload.get("call_sid")
    return VoiceResponse(action="ack", metadata={"provider": "twilio", "call_sid": call_sid})


@app.post("/twilio/stream", response_model=VoiceResponse)
async def handle_twilio_stream(stream_request: StreamRequest, background_tasks: BackgroundTasks) -> VoiceResponse:
    if not stream_request.audio_chunks:
        raise HTTPException(status_code=400, detail="audio_chunks payload is required")

    call_sid = stream_request.call_sid
    locale = stream_request.locale or app.state.settings.transcribe_language_code
    audio_bytes = app.state.transcribe.decode_chunks(stream_request.audio_chunks)
    transcript = await app.state.transcribe.transcribe_audio(
        audio_bytes,
        sample_rate_hz=stream_request.sample_rate_hz,
        encoding=stream_request.encoding,
    )

    if not transcript:
        return VoiceResponse(
            action="ack",
            metadata={"provider": "twilio", "call_sid": call_sid, "locale": locale},
        )

    event_payload = {
        "CallSid": call_sid,
        "transcript": transcript,
        "metadata": stream_request.metadata,
        "source": "media_stream",
    }
    background_tasks.add_task(app.state.event_bus.publish, "call.stream", event_payload)

    await app.state.persistence.upsert_session(
        call_sid,
        {
            "transcript": transcript,
            "locale": locale,
            "metadata": stream_request.metadata,
        },
    )

    orchestrator_raw = await app.state.conversation.advance(call_sid, transcript, locale=locale)
    orchestrator = ConversationResult.model_validate(orchestrator_raw)
    audio = await app.state.speech_pipeline.synthesize(
        orchestrator.response_text,
        speaking_style=orchestrator.directives.get("speaking_style"),
    )

    return VoiceResponse(
        action="play_audio",
        metadata={"provider": "twilio", "call_sid": call_sid, "locale": locale},
        response_text=orchestrator.response_text,
        audio_base64=audio.audio_base64,
        ssml=audio.ssml,
    )


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
