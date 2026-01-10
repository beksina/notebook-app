from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class Difficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class CardType(str, enum.Enum):
    BASIC = "basic"
    CLOZE = "cloze"
    MULTIPLE_CHOICE = "multiple_choice"


class FlashcardDeck(Base):
    __tablename__ = "flashcard_decks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    notebook_id = Column(String, ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    notebook = relationship("Notebook", back_populates="flashcard_decks")
    flashcards = relationship("Flashcard", back_populates="deck", cascade="all, delete-orphan")


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    deck_id = Column(String, ForeignKey("flashcard_decks.id", ondelete="CASCADE"), nullable=False, index=True)
    knowledge_node_id = Column(String, ForeignKey("knowledge_nodes.id", ondelete="SET NULL"), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    difficulty = Column(Enum(Difficulty), default=Difficulty.MEDIUM)
    card_type = Column(Enum(CardType), default=CardType.BASIC)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    next_review_at = Column(DateTime, nullable=True)
    interval_days = Column(Integer, default=1)
    ease_factor = Column(Float, default=2.5)

    # Relationships
    deck = relationship("FlashcardDeck", back_populates="flashcards")
    knowledge_node = relationship("KnowledgeNode", back_populates="flashcards")
    reviews = relationship("CardReview", back_populates="flashcard", cascade="all, delete-orphan")


class CardReview(Base):
    __tablename__ = "card_reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flashcard_id = Column(String, ForeignKey("flashcards.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    quality = Column(Integer, nullable=False)
    reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    time_taken_seconds = Column(Integer, nullable=True)

    # Relationships
    flashcard = relationship("Flashcard", back_populates="reviews")
    user = relationship("User", back_populates="card_reviews")
