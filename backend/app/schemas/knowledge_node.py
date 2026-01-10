from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.knowledge_node import NodeType, MasteryLevel


class KnowledgeNodeBase(BaseModel):
    title: str
    description: Optional[str] = None
    parent_node_id: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    node_type: NodeType = NodeType.LEAF
    mastery_level: MasteryLevel = MasteryLevel.NOT_STARTED
    source_material_id: Optional[str] = None


class KnowledgeNodeCreate(KnowledgeNodeBase):
    pass


class KnowledgeNodeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    parent_node_id: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    node_type: Optional[NodeType] = None
    mastery_level: Optional[MasteryLevel] = None
    source_material_id: Optional[str] = None


class KnowledgeNodeResponse(KnowledgeNodeBase):
    id: str
    notebook_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
