from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotebookBase(BaseModel):
    title: str
    description: Optional[str] = None
    subject_area: Optional[str] = None


class NotebookCreate(NotebookBase):
    pass


class NotebookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subject_area: Optional[str] = None


class NotebookResponse(NotebookBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
