from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class NodeType(str, enum.Enum):
    ROOT = "root"
    BRANCH = "branch"
    LEAF = "leaf"


class MasteryLevel(str, enum.Enum):
    NOT_STARTED = "not_started"
    LEARNING = "learning"
    PRACTICED = "practiced"
    MASTERED = "mastered"


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    notebook_id = Column(String, ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    parent_node_id = Column(String, ForeignKey("knowledge_nodes.id", ondelete="SET NULL"), nullable=True)
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)
    node_type = Column(Enum(NodeType), default=NodeType.LEAF)
    mastery_level = Column(Enum(MasteryLevel), default=MasteryLevel.NOT_STARTED)
    source_material_id = Column(String, ForeignKey("source_materials.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    notebook = relationship("Notebook", back_populates="knowledge_nodes")
    source_material = relationship("SourceMaterial", back_populates="knowledge_nodes")
    parent = relationship("KnowledgeNode", remote_side=[id], backref="children")
    flashcards = relationship("Flashcard", back_populates="knowledge_node")
    quiz_questions = relationship("QuizQuestion", back_populates="knowledge_node")
