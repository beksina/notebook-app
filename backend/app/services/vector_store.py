"""Vector store service using ChromaDB for document embeddings."""

from typing import List, Dict, Any, Optional
import logging

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.services.embeddings import get_embeddings_service

logger = logging.getLogger(__name__)


class VectorStoreService:
    """ChromaDB vector store operations."""

    def __init__(self):
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=str(settings.CHROMA_PERSIST_DIR),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )

    def add_documents(
        self,
        chunks: List[str],
        source_material_id: str,
        notebook_id: str,
        user_id: str,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Add document chunks to vector store with metadata.
        Returns list of chunk IDs.
        """
        if not chunks:
            return []

        # Generate embeddings
        embeddings_svc = get_embeddings_service()
        embeddings = embeddings_svc.generate_embeddings(chunks)

        # Create IDs and metadata for each chunk
        ids = [f"{source_material_id}_chunk_{i}" for i in range(len(chunks))]

        metadatas = []
        for i, chunk in enumerate(chunks):
            metadata = {
                "source_material_id": source_material_id,
                "notebook_id": notebook_id,
                "user_id": user_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            if additional_metadata:
                metadata.update(additional_metadata)
            metadatas.append(metadata)

        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )

        logger.info(f"Added {len(chunks)} chunks for source material {source_material_id}")
        return ids

    def query(
        self,
        query_text: str,
        notebook_id: Optional[str] = None,
        user_id: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query vector store for similar documents.
        Returns list of results with text, metadata, and similarity score.
        """
        # Generate query embedding
        embeddings_svc = get_embeddings_service()
        query_embedding = embeddings_svc.generate_embedding(query_text)

        # Build where clause for filtering
        where = {}
        if notebook_id:
            where["notebook_id"] = notebook_id
        # if user_id:
        #     where["user_id"] = user_id

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where if where else None,
            include=["documents", "metadatas", "distances"]
        )

        # Format results
        formatted = []
        if results["ids"] and results["ids"][0]:
            for i, id in enumerate(results["ids"][0]):
                formatted.append({
                    "id": id,
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "similarity": 1 - results["distances"][0][i]  # Convert distance to similarity
                })

        return formatted

    def delete_by_source_material(self, source_material_id: str) -> int:
        """Delete all chunks for a source material. Returns count deleted."""
        # Get all chunk IDs for this source material
        results = self.collection.get(
            where={"source_material_id": source_material_id},
            include=[]
        )

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(f"Deleted {len(results['ids'])} chunks for source material {source_material_id}")
            return len(results["ids"])
        return 0

    def delete_by_notebook(self, notebook_id: str) -> int:
        """Delete all chunks for a notebook. Returns count deleted."""
        results = self.collection.get(
            where={"notebook_id": notebook_id},
            include=[]
        )

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(f"Deleted {len(results['ids'])} chunks for notebook {notebook_id}")
            return len(results["ids"])
        return 0


# Singleton - lazy initialization
_vector_store = None


def get_vector_store() -> VectorStoreService:
    """Get or create vector store singleton."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store


vector_store = get_vector_store
