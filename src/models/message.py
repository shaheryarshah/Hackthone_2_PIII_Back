from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from .conversation import Conversation


class MessageBase(SQLModel):
    conversation_id: uuid.UUID
    sender_type: str = Field(regex="^(user|assistant)$")  # Enum: 'user', 'assistant'
    content: str = Field(max_length=10000)
    language: str = Field(max_length=10)  # Language code: 'en', 'ur', etc.
    message_type: str = Field(default="text", regex="^(text|voice_transcript|task_action|system)$")
    metadata_json: Optional[str] = Field(default=None)


class Message(MessageBase, table=True):
    """
    Represents a single message in a conversation (from user or AI)
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    conversation: "Conversation" = Relationship(back_populates="messages")


class MessageCreate(MessageBase):
    pass


class MessageRead(MessageBase):
    id: uuid.UUID
    timestamp: datetime