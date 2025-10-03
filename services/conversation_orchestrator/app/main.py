from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
import redis.asyncio as redis

from .config import get_settings
from .dialogue import DialogueManager
from .llm import LLMClient
from .persistence import TranscriptLogger
from .schemas import ConversationRequest, ConversationResponse, SessionState
from .state import SessionStateStore

logger = logging.getLogger(__name__)

app = FastAPI(title="Conversation Orchestrator", version="0.2.0")


@app.on_event("startup")
async def startup_event() -> None:
    settings = get_settings()
    app.state.settings = settings
    app.state.redis = redis.from_url(settings.redis_url, decode_responses=True)
    app.state.state_store = SessionStateStore(app.state.redis, settings.redis_ttl_seconds)
    app.state.llm = LLMClient(settings.openai_api_key)
    app.state.dialogue = DialogueManager(app.state.llm)
    app.state.transcript_logger = TranscriptLogger(str(settings.backend_api_url))
    logger.info("Conversation orchestrator ready")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await app.state.transcript_logger.close()
    await app.state.redis.close()
    await app.state.redis.wait_closed()


@app.post("/conversation", response_model=ConversationResponse)
async def converse(request: ConversationRequest) -> ConversationResponse:
    if not request.user_input.strip():
        raise HTTPException(status_code=400, detail="user_input cannot be empty")

    state: SessionState = await app.state.state_store.load(request.session_id)
    if request.locale:
        state.locale = request.locale

    attributes = {"metadata": request.metadata, "slots": state.slots, "locale": state.locale}
    await app.state.transcript_logger.ensure_session(request.session_id, attributes)

    current_turn = state.turn_index
    updated_state, response_text, directives = await app.state.dialogue.handle_turn(
        state, request.user_input, request.metadata
    )
    await app.state.state_store.save(updated_state)
    await app.state.transcript_logger.ensure_session(
        request.session_id,
        {"metadata": request.metadata, "slots": updated_state.slots, "locale": updated_state.locale},
    )

    # Persist user/assistant transcript segments
    user_message = updated_state.history[-2]
    assistant_message = updated_state.history[-1]
    await app.state.transcript_logger.append_segment(
        request.session_id,
        role=user_message.role,
        content=user_message.content,
        sequence=current_turn * 2,
        locale=updated_state.locale,
    )
    await app.state.transcript_logger.append_segment(
        request.session_id,
        role=assistant_message.role,
        content=assistant_message.content,
        sequence=current_turn * 2 + 1,
        locale=updated_state.locale,
    )

    return ConversationResponse(
        session_id=request.session_id,
        response_text=response_text,
        ssml=directives.get("ssml"),
        state=updated_state,
        directives=directives,
    )


@app.get("/sessions/{session_id}", response_model=SessionState)
async def get_session(session_id: str) -> SessionState:
    state = await app.state.state_store.load(session_id)
    return state


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
