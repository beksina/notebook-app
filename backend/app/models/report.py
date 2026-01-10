from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class ReportType(str, enum.Enum):
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_REVIEW = "weekly_review"
    SESSION_SUMMARY = "session_summary"


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    notebook_id = Column(String, ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(Enum(ReportType), nullable=False)
    content = Column(Text, nullable=True)
    stats = Column(JSON, nullable=True)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="reports")
    notebook = relationship("Notebook", back_populates="reports")
