from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class SessionState(BaseModel):
    session_id: str
    locale: str = "es-MX"
    status: Literal["collecting", "ready", "complete"] = "collecting"
    slots: dict[str, str] = Field(default_factory=dict)
    history: list[ConversationMessage] = Field(default_factory=list)
    turn_index: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationRequest(BaseModel):
    session_id: str
    user_input: str
    locale: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationResponse(BaseModel):
    session_id: str
    response_text: str
    ssml: str | None = None
    state: SessionState
    directives: dict[str, Any] = Field(default_factory=dict)
