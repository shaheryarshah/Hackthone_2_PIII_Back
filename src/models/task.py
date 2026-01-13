from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from .conversation import Conversation


class TaskBase(SQLModel):
    title: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    status: str = Field(default="pending", regex="^(pending|in_progress|completed|cancelled)$")
    priority: str = Field(default="medium", regex="^(low|medium|high|urgent)$")
    due_date: Optional[datetime] = Field(default=None)
    conversation_id: Optional[uuid.UUID] = Field(default=None, foreign_key="conversation.id")


class Task(TaskBase, table=True):
    """
    Represents a user's to-do item with properties like title, description, status, due date, and priority
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    # Relationships
    conversation: Optional["Conversation"] = Relationship(back_populates="tasks")


class TaskCreate(TaskBase):
    title: str


class TaskRead(TaskBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]


class TaskUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None