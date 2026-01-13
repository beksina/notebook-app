from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class HighlightColor(str, enum.Enum):
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PINK = "pink"


class Highlight(Base):
    __tablename__ = "highlights"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_material_id = Column(String, ForeignKey("source_materials.id", ondelete="CASCADE"), nullable=False, index=True)

    # Position tracking (JSON for flexibility across file types)
    # Text/MD: {"start_offset": int, "end_offset": int}
    # PDF: {"page": int, "start_offset": int, "end_offset": int}
    # DOCX: {"start_offset": int, "end_offset": int} (in converted HTML)
    position = Column(JSON, nullable=False)

    # The actual highlighted text (stored for display even if position changes)
    selected_text = Column(Text, nullable=False)

    # Highlight properties
    color = Column(Enum(HighlightColor), default=HighlightColor.YELLOW, nullable=False)

    # Optional note content
    note = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    source_material = relationship("SourceMaterial", back_populates="highlights")
