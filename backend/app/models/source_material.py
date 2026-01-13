from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class SourceType(str, enum.Enum):
    PDF = "pdf"
    URL = "url"
    VIDEO = "video"
    NOTE = "note"
    UPLOAD = "upload"


class SourceMaterial(Base):
    __tablename__ = "source_materials"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    notebook_id = Column(String, ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(SourceType), nullable=False)
    title = Column(String, nullable=False)
    content_url = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed = Column(Boolean, default=False)
    metadata_ = Column("metadata", JSON, nullable=True)  # renamed from "metadata" to avoid shadowing

    # Relationships
    notebook = relationship("Notebook", back_populates="source_materials")
    knowledge_nodes = relationship("KnowledgeNode", back_populates="source_material")
    flashcards = relationship("Flashcard", back_populates="source_material")
    highlights = relationship("Highlight", back_populates="source_material", cascade="all, delete-orphan")
