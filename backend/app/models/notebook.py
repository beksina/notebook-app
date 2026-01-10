from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.database import Base


class Notebook(Base):
    __tablename__ = "notebooks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    subject_area = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="notebooks")
    source_materials = relationship("SourceMaterial", back_populates="notebook", cascade="all, delete-orphan")
    knowledge_nodes = relationship("KnowledgeNode", back_populates="notebook", cascade="all, delete-orphan")
    flashcard_decks = relationship("FlashcardDeck", back_populates="notebook", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="notebook", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="notebook", cascade="all, delete-orphan")
