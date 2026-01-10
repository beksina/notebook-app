from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum


class ChatMessageInput(BaseModel):
    """A single message in chat history (for request)."""
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""
    message: str = Field(..., min_length=1, description="The user's current message")
    history: list[ChatMessageInput] = Field(
        default_factory=list,
        description="Previous messages in the conversation"
    )
    n_results: int = Field(default=5, ge=1, le=10, description="Number of RAG results to retrieve")


class SSEEventType(str, Enum):
    """Event types for SSE streaming."""
    STATUS = "status"
    CONTENT = "content"
    SOURCES = "sources"
    ERROR = "error"
    DONE = "done"