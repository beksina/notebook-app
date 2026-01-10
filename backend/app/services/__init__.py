"""Services for file storage, document processing, and RAG indexing."""

from app.services.storage import storage, StorageBackend, LocalStorageBackend
from app.services.document_processor import document_processor, DocumentProcessor
from app.services.text_chunker import text_chunker, TextChunker
from app.services.embeddings import get_embeddings_service, EmbeddingsService
from app.services.vector_store import get_vector_store, VectorStoreService
from app.services.indexing import indexing_service, IndexingService

__all__ = [
    "storage",
    "StorageBackend",
    "LocalStorageBackend",
    "document_processor",
    "DocumentProcessor",
    "text_chunker",
    "TextChunker",
    "get_embeddings_service",
    "EmbeddingsService",
    "get_vector_store",
    "VectorStoreService",
    "indexing_service",
    "IndexingService",
]
