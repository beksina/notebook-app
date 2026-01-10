"""Embeddings service using OpenAI API."""

from typing import List

from openai import OpenAI

from app.core.config import settings


class EmbeddingsService:
    """Generate embeddings using OpenAI API."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (batched)."""
        if not texts:
            return []

        # OpenAI allows batching - process in batches of 100 for safety
        all_embeddings = []
        batch_size = 100

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.client.embeddings.create(
                model=self.model,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings


# Singleton - lazy initialization to avoid loading without API key
_embeddings_service = None


def get_embeddings_service() -> EmbeddingsService:
    """Get or create embeddings service singleton."""
    global _embeddings_service
    if _embeddings_service is None:
        _embeddings_service = EmbeddingsService()
    return _embeddings_service


embeddings_service = get_embeddings_service
