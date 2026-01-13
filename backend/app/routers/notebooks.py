from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pathlib import Path
import logging
import json
import mimetypes

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
from app.schemas.flashcard import (
    FlashcardDeckCreate, FlashcardDeckUpdate, FlashcardDeckResponse,
    FlashcardCreate, FlashcardUpdate, FlashcardResponse,
    GenerateCardsRequest, GeneratedCard,
    CardReviewCreate, CardReviewResponse
)
from app.models.flashcard import FlashcardDeck, Flashcard, CardReview
from app.models.highlight import Highlight
from app.schemas.highlight import HighlightCreate, HighlightUpdate, HighlightResponse
from datetime import timedelta
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


# # Source Material endpoints (nested under notebooks)
# @router.post("/{notebook_id}/materials", response_model=SourceMaterialResponse, status_code=201)
# def create_source_material(
#     notebook_id: str, 
#     material: SourceMaterialCreate, 
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     notebook = db.query(Notebook).filter(
#         Notebook.id == notebook_id,
#         Notebook.user_id == current_user.id
#     ).first()

#     if not notebook:
#         raise HTTPException(status_code=404, detail="Notebook not found")

#     db_material = SourceMaterial(**material.model_dump(), notebook_id=notebook_id)
#     db.add(db_material)
#     db.commit()
#     db.refresh(db_material)
#     return db_material


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


@router.get("/{notebook_id}/materials/{material_id}/content")
async def get_material_content(
    notebook_id: str,
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Serve the raw file content for a source material.
    Returns the file with appropriate content-type header.
    """
    # Verify notebook ownership
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    # Get material
    material = db.query(SourceMaterial).filter(
        SourceMaterial.id == material_id,
        SourceMaterial.notebook_id == notebook_id
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="Source material not found")

    if not material.content_url:
        raise HTTPException(status_code=404, detail="Material has no file content")

    # Get file content from storage
    try:
        content = await storage.get(material.content_url)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found in storage")

    # Determine content type from file extension
    content_type, _ = mimetypes.guess_type(material.content_url)
    if not content_type:
        content_type = "application/octet-stream"

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{material.title}"'
        }
    )


# ==================== Highlight endpoints ====================

@router.post("/{notebook_id}/materials/{material_id}/highlights",
             response_model=HighlightResponse, status_code=201)
def create_highlight(
    notebook_id: str,
    material_id: str,
    highlight: HighlightCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new highlight on a source material."""
    # Verify notebook ownership
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    # Verify material belongs to notebook
    material = db.query(SourceMaterial).filter(
        SourceMaterial.id == material_id,
        SourceMaterial.notebook_id == notebook_id
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="Source material not found")

    db_highlight = Highlight(
        **highlight.model_dump(),
        source_material_id=material_id
    )
    db.add(db_highlight)
    db.commit()
    db.refresh(db_highlight)
    return db_highlight


@router.get("/{notebook_id}/materials/{material_id}/highlights",
            response_model=List[HighlightResponse])
def list_highlights(
    notebook_id: str,
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all highlights for a source material."""
    # Verify access
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    material = db.query(SourceMaterial).filter(
        SourceMaterial.id == material_id,
        SourceMaterial.notebook_id == notebook_id
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="Source material not found")

    return db.query(Highlight).filter(
        Highlight.source_material_id == material_id
    ).order_by(Highlight.created_at).all()


@router.patch("/{notebook_id}/materials/{material_id}/highlights/{highlight_id}",
              response_model=HighlightResponse)
def update_highlight(
    notebook_id: str,
    material_id: str,
    highlight_id: str,
    highlight_update: HighlightUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a highlight (color or note)."""
    # Verify access chain
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    highlight = db.query(Highlight).join(SourceMaterial).filter(
        Highlight.id == highlight_id,
        Highlight.source_material_id == material_id,
        SourceMaterial.notebook_id == notebook_id
    ).first()
    if not highlight:
        raise HTTPException(status_code=404, detail="Highlight not found")

    update_data = highlight_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(highlight, field, value)

    db.commit()
    db.refresh(highlight)
    return highlight


@router.delete("/{notebook_id}/materials/{material_id}/highlights/{highlight_id}",
               status_code=204)
def delete_highlight(
    notebook_id: str,
    material_id: str,
    highlight_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a highlight."""
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    highlight = db.query(Highlight).join(SourceMaterial).filter(
        Highlight.id == highlight_id,
        Highlight.source_material_id == material_id,
        SourceMaterial.notebook_id == notebook_id
    ).first()
    if not highlight:
        raise HTTPException(status_code=404, detail="Highlight not found")

    db.delete(highlight)
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


# ==================== Deck endpoints ====================

@router.get("/{notebook_id}/decks", response_model=List[FlashcardDeckResponse])
def list_decks(
    notebook_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all decks in a notebook."""
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    decks = db.query(FlashcardDeck).filter(FlashcardDeck.notebook_id == notebook_id).all()

    # Add card count to each deck
    result = []
    for deck in decks:
        card_count = db.query(Flashcard).filter(Flashcard.deck_id == deck.id).count()
        deck_dict = {
            "id": deck.id,
            "notebook_id": deck.notebook_id,
            "title": deck.title,
            "created_at": deck.created_at,
            "card_count": card_count
        }
        result.append(FlashcardDeckResponse(**deck_dict))

    return result


@router.post("/{notebook_id}/decks", response_model=FlashcardDeckResponse, status_code=201)
def create_deck(
    notebook_id: str,
    deck: FlashcardDeckCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new deck in a notebook."""
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    db_deck = FlashcardDeck(**deck.model_dump(), notebook_id=notebook_id)
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)

    return FlashcardDeckResponse(
        id=db_deck.id,
        notebook_id=db_deck.notebook_id,
        title=db_deck.title,
        created_at=db_deck.created_at,
        card_count=0
    )


@router.get("/{notebook_id}/decks/{deck_id}", response_model=FlashcardDeckResponse)
def get_deck(
    notebook_id: str,
    deck_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific deck."""
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    deck = db.query(FlashcardDeck).filter(
        FlashcardDeck.id == deck_id,
        FlashcardDeck.notebook_id == notebook_id
    ).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    card_count = db.query(Flashcard).filter(Flashcard.deck_id == deck.id).count()

    return FlashcardDeckResponse(
        id=deck.id,
        notebook_id=deck.notebook_id,
        title=deck.title,
        created_at=deck.created_at,
        card_count=card_count
    )


@router.patch("/{notebook_id}/decks/{deck_id}", response_model=FlashcardDeckResponse)
def update_deck(
    notebook_id: str,
    deck_id: str,
    deck_update: FlashcardDeckUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a deck."""
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    deck = db.query(FlashcardDeck).filter(
        FlashcardDeck.id == deck_id,
        FlashcardDeck.notebook_id == notebook_id
    ).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    update_data = deck_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(deck, field, value)

    db.commit()
    db.refresh(deck)

    card_count = db.query(Flashcard).filter(Flashcard.deck_id == deck.id).count()

    return FlashcardDeckResponse(
        id=deck.id,
        notebook_id=deck.notebook_id,
        title=deck.title,
        created_at=deck.created_at,
        card_count=card_count
    )


@router.delete("/{notebook_id}/decks/{deck_id}", status_code=204)
def delete_deck(
    notebook_id: str,
    deck_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a deck and all its cards."""
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    deck = db.query(FlashcardDeck).filter(
        FlashcardDeck.id == deck_id,
        FlashcardDeck.notebook_id == notebook_id
    ).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    db.delete(deck)
    db.commit()


# ==================== Card endpoints ====================

@router.get("/{notebook_id}/decks/{deck_id}/cards", response_model=List[FlashcardResponse])
def list_cards(
    notebook_id: str,
    deck_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all cards in a deck."""
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    deck = db.query(FlashcardDeck).filter(
        FlashcardDeck.id == deck_id,
        FlashcardDeck.notebook_id == notebook_id
    ).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    return db.query(Flashcard).filter(Flashcard.deck_id == deck_id).all()


@router.post("/{notebook_id}/decks/{deck_id}/cards", response_model=FlashcardResponse, status_code=201)
def create_card(
    notebook_id: str,
    deck_id: str,
    card: FlashcardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new card in a deck."""
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    deck = db.query(FlashcardDeck).filter(
        FlashcardDeck.id == deck_id,
        FlashcardDeck.notebook_id == notebook_id
    ).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    db_card = Flashcard(**card.model_dump(), deck_id=deck_id)
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card


@router.patch("/{notebook_id}/cards/{card_id}", response_model=FlashcardResponse)
def update_card(
    notebook_id: str,
    card_id: str,
    card_update: FlashcardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a card."""
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    card = db.query(Flashcard).join(FlashcardDeck).filter(
        Flashcard.id == card_id,
        FlashcardDeck.notebook_id == notebook_id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    update_data = card_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(card, field, value)

    db.commit()
    db.refresh(card)
    return card


@router.delete("/{notebook_id}/cards/{card_id}", status_code=204)
def delete_card(
    notebook_id: str,
    card_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a card."""
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    card = db.query(Flashcard).join(FlashcardDeck).filter(
        Flashcard.id == card_id,
        FlashcardDeck.notebook_id == notebook_id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    db.delete(card)
    db.commit()


# ==================== Card generation endpoint ====================

@router.post("/{notebook_id}/decks/{deck_id}/generate")
async def generate_cards(
    notebook_id: str,
    deck_id: str,
    request: GenerateCardsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate flashcards from notebook documents using LLM.
    Streams SSE events with generated cards.
    """
    # Verify notebook ownership
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    # Verify deck exists
    deck = db.query(FlashcardDeck).filter(
        FlashcardDeck.id == deck_id,
        FlashcardDeck.notebook_id == notebook_id
    ).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    # Get source materials to generate from
    materials_query = db.query(SourceMaterial).filter(
        SourceMaterial.notebook_id == notebook_id,
        SourceMaterial.processed == True
    )
    if request.source_material_ids:
        materials_query = materials_query.filter(
            SourceMaterial.id.in_(request.source_material_ids)
        )
    materials = materials_query.all()

    if not materials:
        raise HTTPException(
            status_code=400,
            detail="No processed documents found to generate cards from"
        )

    async def event_generator():
        vs = get_vector_store()

        try:
            yield {
                "event": SSEEventType.STATUS.value,
                "data": json.dumps({"message": "Retrieving document content..."})
            }

            # Get chunks from vector store for each material
            all_chunks = []
            for material in materials:
                # Get all chunks for this material without embedding search
                results = vs.get_documents(
                    source_material_id=material.id,
                    limit=50  # Get up to 50 chunks per material
                )
                for r in results:
                    all_chunks.append({
                        "text": r["text"],
                        "source_material_id": material.id,
                        "source_title": material.title
                    })

            if not all_chunks:
                yield {
                    "event": SSEEventType.ERROR.value,
                    "data": json.dumps({"message": "No content found in documents"})
                }
                return

            yield {
                "event": SSEEventType.STATUS.value,
                "data": json.dumps({"message": f"Generating cards from {len(all_chunks)} text chunks..."})
            }

            # Generate cards using LLM
            cards = await llm_service.generate_flashcards(
                chunks=all_chunks,
                max_cards=request.max_cards
            )

            # Save cards to database and stream them
            db_session = SessionLocal()
            try:
                for card_data in cards:
                    db_card = Flashcard(
                        deck_id=deck_id,
                        question=card_data["question"],
                        answer=card_data["answer"],
                        source_material_id=card_data.get("source_material_id")
                    )
                    db_session.add(db_card)
                    db_session.commit()
                    db_session.refresh(db_card)

                    yield {
                        "event": "card",
                        "data": json.dumps({
                            "id": db_card.id,
                            "question": db_card.question,
                            "answer": db_card.answer,
                            "source_material_id": db_card.source_material_id
                        })
                    }
            finally:
                db_session.close()

            yield {
                "event": SSEEventType.DONE.value,
                "data": json.dumps({"message": f"Generated {len(cards)} cards"})
            }

        except Exception as e:
            logger.exception(f"Card generation error: {e}")
            yield {
                "event": SSEEventType.ERROR.value,
                "data": json.dumps({"message": str(e)})
            }

    return EventSourceResponse(event_generator())


# ==================== Card review endpoint ====================

@router.post("/{notebook_id}/cards/{card_id}/review", response_model=CardReviewResponse, status_code=201)
def review_card(
    notebook_id: str,
    card_id: str,
    review: CardReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Record a card review and update spaced repetition parameters.

    Quality ratings (SM-2 scale):
    - 1: Complete blackout, wrong response
    - 2: Wrong response, but upon seeing answer, remembered
    - 3: Correct response with serious difficulty
    - 4: Correct response after hesitation
    - 5: Perfect response, instant recall

    For simplicity, frontend can use:
    - "Forgot" = quality 1-2
    - "Hard" = quality 3
    - "Good" = quality 4
    - "Easy" = quality 5
    """
    # Verify notebook ownership
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    # Get card and verify it belongs to this notebook
    card = db.query(Flashcard).join(FlashcardDeck).filter(
        Flashcard.id == card_id,
        FlashcardDeck.notebook_id == notebook_id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Create review record
    from datetime import datetime, timezone
    db_review = CardReview(
        flashcard_id=card_id,
        user_id=current_user.id,
        quality=review.quality,
        time_taken_seconds=review.time_taken_seconds
    )
    db.add(db_review)

    # Update card SRS parameters using SM-2 algorithm
    quality = review.quality

    if quality < 3:
        # Failed recall - reset to 1 day
        card.interval_days = 1
    else:
        # Successful recall - increase interval
        if card.interval_days == 1:
            card.interval_days = 6
        else:
            card.interval_days = int(card.interval_days * card.ease_factor)

    # Update ease factor (minimum 1.3)
    card.ease_factor = max(
        1.3,
        card.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    )

    # Set next review date
    card.next_review_at = datetime.now(timezone.utc) + timedelta(days=card.interval_days)

    db.commit()
    db.refresh(db_review)

    return db_review


@router.get("/{notebook_id}/cards/{card_id}", response_model=FlashcardResponse)
def get_card(
    notebook_id: str,
    card_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single card with its current spaced repetition state."""
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    card = db.query(Flashcard).join(FlashcardDeck).filter(
        Flashcard.id == card_id,
        FlashcardDeck.notebook_id == notebook_id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    return card
