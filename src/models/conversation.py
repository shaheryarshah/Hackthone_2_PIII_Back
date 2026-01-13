from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from .message import Message
    from .user import User


class ConversationBase(SQLModel):
    title: str = Field(default="New Conversation", max_length=255)
    language_preference: str = Field(default="en", max_length=10)
    metadata_json: Optional[str] = Field(default=None)


class Conversation(ConversationBase, table=True):
    """
    Represents a chat session between user and AI assistant, including message history and metadata
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    messages: list["Message"] = Relationship(back_populates="conversation")
    user: Optional["User"] = Relationship(back_populates="conversations")


class ConversationCreate(ConversationBase):
    pass


class ConversationRead(ConversationBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime