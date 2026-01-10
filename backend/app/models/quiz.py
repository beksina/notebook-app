from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class QuizType(str, enum.Enum):
    DAILY_STARTER = "daily_starter"
    WEEKLY_COMPREHENSIVE = "weekly_comprehensive"
    CUSTOM = "custom"


class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    TRUE_FALSE = "true_false"


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    notebook_id = Column(String, ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True)
    quiz_type = Column(Enum(QuizType), nullable=False)
    knowledge_node_ids = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    scheduled_for = Column(DateTime, nullable=True)

    # Relationships
    notebook = relationship("Notebook", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    knowledge_node_id = Column(String, ForeignKey("knowledge_nodes.id", ondelete="SET NULL"), nullable=True)
    question = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionType), default=QuestionType.MULTIPLE_CHOICE)
    options = Column(JSON, nullable=True)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    knowledge_node = relationship("KnowledgeNode", back_populates="quiz_questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Float, nullable=True)
    answers = Column(JSON, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    time_taken_minutes = Column(Integer, nullable=True)

    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    user = relationship("User", back_populates="quiz_attempts")
