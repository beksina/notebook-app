from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pathlib import Path
import logging
import json

from sse_starlette.sse import EventSourceResponse

from app.database import get_db, SessionLocal
from app.models.notebook import Notebook
from app.models.user import User
from app.models.source_material import SourceMaterial, SourceType
from app.schemas.notebook import NotebookCreate, NotebookUpdate, NotebookResponse
from app.schemas.source_material import (
    SourceMaterialCreate,
    SourceMaterialUpdate,
    SourceMaterialResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGChunkResult
)
from app.routers.auth import get_current_user
from app.services.storage import storage
from app.services.indexing import indexing_service
from app.services.vector_store import get_vector_store
from app.services.llm import llm_service
from app.schemas.chat_message import ChatRequest, SSEEventType
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


@router.post("/", response_model=NotebookResponse, status_code=201)
def create_notebook(
    notebook: NotebookCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_notebook = Notebook(**notebook.model_dump(), user_id=current_user.id)
    db.add(db_notebook)
    db.commit()
    db.refresh(db_notebook)
    return db_notebook


    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")

    # db_notebook = Notebook(**notebook.model_dump(), user_id=user_id)
    # db.add(db_notebook)
    # db.commit()
    # db.refresh(db_notebook)
    # return db_notebook


@router.get("/", response_model=List[NotebookResponse])
def list_notebooks(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Notebook)
    query = query.filter(Notebook.user_id == current_user.id)
    return query.offset(skip).limit(limit).all()


@router.get("/{notebook_id}", response_model=NotebookResponse)
def get_notebook(
    notebook_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()

    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return notebook


@router.patch("/{notebook_id}", response_model=NotebookResponse)
def update_notebook(
    notebook_id: str, 
    notebook_update: NotebookUpdate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()

    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    update_data = notebook_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(notebook, field, value)

    db.commit()
    db.refresh(notebook)
    return notebook


@router.delete("/{notebook_id}", status_code=204)
def delete_notebook(
    notebook_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()

    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    db.delete(notebook)
    db.commit()


# Source Material endpoints (nested under notebooks)
@router.post("/{notebook_id}/materials", response_model=SourceMaterialResponse, status_code=201)
def create_source_material(
    notebook_id: str, 
    material: SourceMaterialCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()

    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    db_material = SourceMaterial(**material.model_dump(), notebook_id=notebook_id)
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material


@router.get("/{notebook_id}/materials", response_model=List[SourceMaterialResponse])
def list_source_materials(
    notebook_id: str, 
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    return db.query(SourceMaterial).filter(SourceMaterial.notebook_id == notebook_id).offset(skip).limit(limit).all()
  

# TODO: add auth
@router.get("/{notebook_id}/materials/{material_id}", response_model=SourceMaterialResponse)
def get_source_material(
    notebook_id: str, 
    material_id: str, 
    db: Session = Depends(get_db)
):
    material = db.query(SourceMaterial).filter(
        SourceMaterial.id == material_id,
        SourceMaterial.notebook_id == notebook_id
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="Source material not found")
    return material

# TODO: add auth
@router.patch("/{notebook_id}/materials/{material_id}", response_model=SourceMaterialResponse)
def update_source_material(notebook_id: str, material_id: str, material_update: SourceMaterialUpdate, db: Session = Depends(get_db)):
    material = db.query(SourceMaterial).filter(
        SourceMaterial.id == material_id,
        SourceMaterial.notebook_id == notebook_id
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="Source material not found")

    update_data = material_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material, field, value)

    db.commit()
    db.refresh(material)
    return material

@router.delete("/{notebook_id}/materials/{material_id}", status_code=204)
async def delete_source_material(
    notebook_id: str,
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    )
    if not notebook: 
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    material = db.query(SourceMaterial).filter(
        SourceMaterial.id == material_id,
        SourceMaterial.notebook_id == notebook_id
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="Source material not found")

    # Delete from vector store first
    indexing_service.delete_document_index(material_id)

    # Delete physical file from storage
    if material.content_url:
        await storage.delete(material.content_url)

    db.delete(material)
    db.commit()


# File upload endpoint
@router.post("/{notebook_id}/materials/upload", response_model=SourceMaterialResponse, status_code=201)
async def upload_source_material(
    notebook_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a file as source material.
    Supports: PDF, TXT, MD, DOCX
    File is saved and indexed asynchronously.
    """
    # Verify notebook ownership
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()

    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Validate file size (read content to check)
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Reset file position for storage
    await file.seek(0)

    # Determine source type from extension
    ext_to_type = {
        ".pdf": SourceType.PDF,
        ".txt": SourceType.UPLOAD,
        ".md": SourceType.UPLOAD,
        ".docx": SourceType.UPLOAD,
    }
    source_type = ext_to_type.get(file_ext, SourceType.UPLOAD)

    # Save file to storage
    storage_path = await storage.save(file, current_user.id, notebook_id)

    # Create database record
    db_material = SourceMaterial(
        notebook_id=notebook_id,
        type=source_type,
        title=title or file.filename,
        content_url=storage_path,
        processed=False
    )
    db.add(db_material)
    db.commit()
    db.refresh(db_material)

    # Schedule async indexing
    background_tasks.add_task(
        index_document_background,
        source_material_id=db_material.id,
        user_id=current_user.id
    )

    logger.info(f"Uploaded material {db_material.id}, indexing scheduled")

    return db_material


async def index_document_background(source_material_id: str, user_id: str):
    """Background task to index a document."""
    db = SessionLocal()
    try:
        success = await indexing_service.index_document(
            source_material_id=source_material_id,
            user_id=user_id,
            db=db
        )
        if success:
            logger.info(f"Successfully indexed material {source_material_id}")
        else:
            logger.error(f"Failed to index material {source_material_id}")
    except Exception as e:
        logger.exception(f"Error in background indexing: {e}")
    finally:
        db.close()


# RAG Query endpoint
@router.post("/{notebook_id}/query", response_model=RAGQueryResponse)
def query_notebook_documents(
    notebook_id: str,
    query: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Query indexed documents in a notebook using semantic search.
    Returns relevant chunks with source attribution.
    """
    # Verify notebook ownership
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()

    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    # Query vector store
    vs = get_vector_store()
    results = vs.query(
        query_text=query.query,
        notebook_id=notebook_id,
        user_id=current_user.id,
        n_results=query.n_results
    )

    # Format response
    formatted_results = []
    for result in results:
        formatted_results.append(RAGChunkResult(
            text=result["text"],
            source_material_id=result["metadata"]["source_material_id"],
            source_title=result["metadata"].get("title", "Unknown"),
            similarity=result["similarity"],
            chunk_index=result["metadata"]["chunk_index"]
        ))

    return RAGQueryResponse(
        query=query.query,
        results=formatted_results
    )


# Chat endpoint with streaming
@router.post("/{notebook_id}/chat")
async def chat_with_notebook(
    notebook_id: str,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with notebook documents using RAG.
    Streams SSE events: status updates, sources, content chunks, done.
    """
    # Verify notebook ownership
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()

    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    async def event_generator():
        vs = get_vector_store()

        try:
            # Step 1: Query rewriting
            yield {
                "event": SSEEventType.STATUS.value,
                "data": json.dumps({"message": "Analyzing your question..."})
            }

            # Convert history to dict format
            history_dicts = [
                {"role": msg.role, "content": msg.content}
                for msg in chat_request.history
            ]

            # Rewrite query for better RAG retrieval
            rewritten_query = await llm_service.rewrite_query_for_rag(
                message=chat_request.message,
                history=history_dicts
            )

            # Step 2: RAG retrieval
            yield {
                "event": SSEEventType.STATUS.value,
                "data": json.dumps({"message": "Searching documents..."})
            }

            results = vs.query(
                query_text=rewritten_query,
                notebook_id=notebook_id,
                user_id=current_user.id,
                n_results=chat_request.n_results
            )

            # Step 3: Send sources
            sources_data = [
                {
                    "title": r["metadata"].get("title", "Unknown"),
                    "similarity": round(r["similarity"], 2),
                    "preview": r["text"][:150] + "..." if len(r["text"]) > 150 else r["text"]
                }
                for r in results
            ]
            yield {
                "event": SSEEventType.SOURCES.value,
                "data": json.dumps({"sources": sources_data})
            }

            # Step 4: Format context for LLM
            context = _format_context_for_llm(results)

            # Step 5: Stream LLM response
            yield {
                "event": SSEEventType.STATUS.value,
                "data": json.dumps({"message": "Generating response..."})
            }
            
            async for chunk in llm_service.generate_response_stream(
                message=chat_request.message,
                history=history_dicts,
                context=context
            ):
                yield {
                    "event": SSEEventType.CONTENT.value,
                    "data": json.dumps({"text": chunk})
                }

            # Done
            yield {
                "event": SSEEventType.DONE.value,
                "data": json.dumps({})
            }

        except Exception as e:
            logger.exception(f"Chat error: {e}")
            yield {
                "event": SSEEventType.ERROR.value,
                "data": json.dumps({"message": str(e)})
            }

    return EventSourceResponse(event_generator(), ping=100)


def _format_context_for_llm(results: List[dict[str, Any]]) -> str:
    """Format RAG results into context string for LLM."""
    if not results:
        return "No relevant documents found."

    context_parts = []
    for i, result in enumerate(results, 1):
        title = result["metadata"].get("title", "Unknown Document")
        text = result["text"]
        similarity = result["similarity"]
        context_parts.append(
            f"[Document {i}: {title}] (relevance: {similarity:.0%})\n{text}"
        )

    return "\n\n---\n\n".join(context_parts)
