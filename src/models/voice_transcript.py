from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from .message import Message


class VoiceTranscriptBase(SQLModel):
    message_id: uuid.UUID = Field(foreign_key="message.id")
    original_audio_path: Optional[str] = Field(default=None)
    cleaned_text: str = Field(max_length=10000)
    extracted_intent: str = Field(max_length=255)
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time: Optional[float] = Field(default=None)


class VoiceTranscript(VoiceTranscriptBase, table=True):
    """
    Represents processed voice input with cleaned text, extracted intent, and confidence scores
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    message: "Message" = Relationship(back_populates="voice_transcript")


class VoiceTranscriptCreate(VoiceTranscriptBase):
    cleaned_text: str
    extracted_intent: str
    confidence_score: float


class VoiceTranscriptRead(VoiceTranscriptBase):
    id: uuid.UUID
    created_at: datetime