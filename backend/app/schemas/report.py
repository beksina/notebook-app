from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any
from app.models.report import ReportType


class ReportBase(BaseModel):
    report_type: ReportType
    content: Optional[str] = None
    stats: Optional[dict[str, Any]] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class ReportCreate(ReportBase):
    pass


class ReportUpdate(BaseModel):
    content: Optional[str] = None
    stats: Optional[dict[str, Any]] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class ReportResponse(ReportBase):
    id: str
    user_id: str
    notebook_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
