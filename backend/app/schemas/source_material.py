from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any, List
from app.models.source_material import SourceType


class SourceMaterialBase(BaseModel):
    type: SourceType
    title: str
    content_url: Optional[str] = None
    # metadata: Optional[dict[str, Any]] = None


class SourceMaterialCreate(SourceMaterialBase):
    pass


class SourceMaterialUpdate(BaseModel):
    title: Optional[str] = None
    content_url: Optional[str] = None
    processed: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None


class SourceMaterialResponse(SourceMaterialBase):
    id: str
    notebook_id: str
    uploaded_at: datetime
    processed: bool

    model_config = {"from_attributes": True}


# RAG Query Schemas
class RAGQueryRequest(BaseModel):
    """Request for semantic search query."""
    query: str = Field(..., min_length=1, description="The search query")
    n_results: int = Field(default=5, ge=1, le=20, description="Number of results to return")


class RAGChunkResult(BaseModel):
    """A single chunk result from RAG query."""
    text: str
    source_material_id: str
    source_title: str
    similarity: float
    chunk_index: int


class RAGQueryResponse(BaseModel):
    """Response containing RAG query results."""
    query: str
    results: List[RAGChunkResult]
