"""LLM service for chat completions using Anthropic Claude."""

from typing import AsyncGenerator
import anthropic

from app.core.config import settings


class LLMService:
    """Service for Anthropic Claude API interactions."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL

    async def rewrite_query_for_rag(
        self,
        message: str,
        history: list[dict[str, str]]
    ) -> str:
        """
        Rewrite the user's message into an optimized RAG query.
        Uses conversation context to produce a standalone search query.
        """
        system_prompt = """You are a query rewriting assistant. Your task is to transform the user's latest message into an optimized search query for semantic document retrieval.

Rules:
1. Make the query standalone (resolve pronouns, references to previous messages)
2. Extract key concepts and entities
3. Preserve the original intent
4. Output ONLY the rewritten query, nothing else
5. If the message is already a good search query, return it as-is"""

        messages = []
        for msg in history[-6:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        messages.append({
            "role": "user",
            "content": f"Rewrite this message as a search query: {message}"
        })

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=200,
            system=system_prompt,
            messages=messages
        )

        return response.content[0].text.strip()

    async def generate_response_stream(
        self,
        message: str,
        history: list[dict[str, str]],
        context: str
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response using retrieved context.
        Yields text chunks as they arrive.
        """
        system_prompt = f"""You are a helpful assistant answering questions based on the user's documents.

RETRIEVED CONTEXT:
{context}

INSTRUCTIONS:
1. Answer the question using ONLY the information from the retrieved context above
2. If the context doesn't contain relevant information, say so clearly
3. Cite specific parts of the documents when possible, including the document name
4. Be concise but thorough
5. If asked about something not in the context, acknowledge the limitation"""
        messages = []
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        messages.append({
            "role": "user",
            "content": message
        })

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=messages
        ) as stream:
            async for text in stream.text_stream:
                yield text


llm_service = LLMService()
