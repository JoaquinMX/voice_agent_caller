from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import relationship

from .database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    notes = Column(String, nullable=True)


class CallSession(Base):
    __tablename__ = "call_sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    attributes = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    transcripts = relationship("TranscriptSegment", back_populates="session", cascade="all, delete")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey("call_sessions.session_id"), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    locale = Column(String, nullable=False, default="es-MX")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("CallSession", back_populates="transcripts")
