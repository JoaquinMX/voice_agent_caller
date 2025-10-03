from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Voice Agent Backend API", version="0.1.0")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/contacts", response_model=schemas.Contact, status_code=201)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)) -> schemas.Contact:
    db_contact = models.Contact(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return schemas.Contact.model_validate(db_contact)


@app.get("/contacts/{contact_id}", response_model=schemas.Contact)
def read_contact(contact_id: int, db: Session = Depends(get_db)) -> schemas.Contact:
    instance = db.get(models.Contact, contact_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return schemas.Contact.model_validate(instance)


@app.put("/sessions/{session_id}", response_model=schemas.CallSession)
def upsert_session(
    session_id: str, payload: schemas.SessionUpsert, db: Session = Depends(get_db)
) -> schemas.CallSession:
    stmt = select(models.CallSession).where(models.CallSession.session_id == session_id)
    instance = db.execute(stmt).scalar_one_or_none()
    if instance is None:
        instance = models.CallSession(session_id=session_id, attributes=payload.attributes)
        db.add(instance)
    else:
        instance.attributes = payload.attributes or {}
    db.commit()
    db.refresh(instance)
    return schemas.CallSession.model_validate(instance)


@app.get("/sessions/{session_id}", response_model=schemas.CallSession)
def read_session(session_id: str, db: Session = Depends(get_db)) -> schemas.CallSession:
    stmt = select(models.CallSession).where(models.CallSession.session_id == session_id)
    instance = db.execute(stmt).scalar_one_or_none()
    if instance is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return schemas.CallSession.model_validate(instance)


@app.post(
    "/sessions/{session_id}/transcripts",
    response_model=schemas.TranscriptSegment,
    status_code=201,
)
def append_transcript_segment(
    session_id: str,
    segment: schemas.TranscriptSegmentCreate,
    db: Session = Depends(get_db),
) -> schemas.TranscriptSegment:
    stmt = select(models.CallSession).where(models.CallSession.session_id == session_id)
    session = db.execute(stmt).scalar_one_or_none()
    if session is None:
        session = models.CallSession(session_id=session_id, attributes={})
        db.add(session)
        db.flush()

    db_segment = models.TranscriptSegment(
        session_id=session_id,
        sequence=segment.sequence,
        role=segment.role,
        content=segment.content,
        locale=segment.locale,
    )
    db.add(db_segment)
    db.commit()
    db.refresh(db_segment)
    return schemas.TranscriptSegment.model_validate(db_segment)


@app.get(
    "/sessions/{session_id}/transcripts",
    response_model=list[schemas.TranscriptSegment],
)
def list_transcripts(session_id: str, db: Session = Depends(get_db)) -> list[schemas.TranscriptSegment]:
    stmt = (
        select(models.TranscriptSegment)
        .where(models.TranscriptSegment.session_id == session_id)
        .order_by(models.TranscriptSegment.sequence.asc())
    )
    records = db.execute(stmt).scalars().all()
    return [schemas.TranscriptSegment.model_validate(row) for row in records]


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
