"""Indexing service that orchestrates the document processing pipeline."""

import logging
from sqlalchemy.orm import Session

from app.services.storage import storage
from app.services.document_processor import document_processor
from app.services.text_chunker import text_chunker
from app.services.vector_store import get_vector_store
from app.models.source_material import SourceMaterial

logger = logging.getLogger(__name__)


class IndexingService:
    """Orchestrates the document indexing pipeline."""

    async def index_document(
        self,
        source_material_id: str,
        user_id: str,
        db: Session
    ) -> bool:
        """
        Full indexing pipeline for a document.
        1. Retrieve file from storage
        2. Extract text
        3. Chunk text
        4. Generate embeddings and store in vector DB
        5. Mark as processed

        Returns True on success, False on failure.
        """
        try:
            # Get source material record
            material = db.query(SourceMaterial).filter(
                SourceMaterial.id == source_material_id
            ).first()

            if not material:
                logger.error(f"Source material not found: {source_material_id}")
                return False

            if not material.content_url:
                logger.error(f"No content_url for material: {source_material_id}")
                return False

            logger.info(f"Starting indexing for material {source_material_id}")

            # Get file content from storage
            file_content = await storage.get(material.content_url)

            # Extract text based on file type
            # Use the stored filename (last part of path) to determine type
            filename = material.content_url.split("/")[-1]
            text = document_processor.extract_text_from_bytes(file_content, filename)

            if not text.strip():
                logger.warning(f"No text extracted from: {source_material_id}")
                material.processed = True  # Mark as processed even if empty
                db.commit()
                return True

            logger.info(f"Extracted {len(text)} characters from {source_material_id}")

            # Chunk the text
            chunks = text_chunker.chunk_text(text)

            if not chunks:
                logger.warning(f"No chunks generated for: {source_material_id}")
                material.processed = True
                db.commit()
                return True

            logger.info(f"Generated {len(chunks)} chunks for {source_material_id}")

            # Add to vector store
            vs = get_vector_store()
            chunk_ids = vs.add_documents(
                chunks=chunks,
                source_material_id=source_material_id,
                notebook_id=material.notebook_id,
                user_id=user_id,
                additional_metadata={
                    "title": material.title,
                    "source_type": material.type.value if material.type else "unknown"
                }
            )

            logger.info(f"Indexed {len(chunks)} chunks for material {source_material_id}")

            # Mark as processed
            material.processed = True
            db.commit()

            return True

        except Exception as e:
            logger.exception(f"Error indexing document {source_material_id}: {e}")
            return False

    def delete_document_index(self, source_material_id: str) -> int:
        """Remove document from vector store."""
        vs = get_vector_store()
        return vs.delete_by_source_material(source_material_id)


# Singleton
indexing_service = IndexingService()
