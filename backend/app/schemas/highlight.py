from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

from app.models.highlight import HighlightColor


class HighlightBase(BaseModel):
    position: Dict[str, Any]  # Flexible JSON structure for different file types
    selected_text: str
    color: HighlightColor = HighlightColor.YELLOW
    note: Optional[str] = None


class HighlightCreate(HighlightBase):
    pass


class HighlightUpdate(BaseModel):
    color: Optional[HighlightColor] = None
    note: Optional[str] = None


class HighlightResponse(HighlightBase):
    id: str
    source_material_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
