from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContactBase(BaseModel):
    phone_number: str = Field(description="E.164 formatted phone number")
    name: str | None = Field(default=None)
    email: str | None = Field(default=None)
    notes: str | None = Field(default=None)


class ContactCreate(ContactBase):
    pass


class Contact(ContactBase):
    id: int

    class Config:
        from_attributes = True


class SessionUpsert(BaseModel):
    attributes: dict[str, Any] = Field(default_factory=dict)


class CallSession(BaseModel):
    session_id: str
    attributes: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TranscriptSegmentCreate(BaseModel):
    role: str
    content: str
    sequence: int
    locale: str = Field(default="es-MX")


class TranscriptSegment(BaseModel):
    id: int
    session_id: str
    sequence: int
    role: str
    content: str
    locale: str
    created_at: datetime

    class Config:
        from_attributes = True
