"""LLM service for chat completions using Anthropic Claude."""

from typing import AsyncGenerator, List, Dict, Any
import anthropic
import json
import re

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

    async def generate_flashcards(
        self,
        chunks: List[Dict[str, Any]],
        max_cards: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate flashcards from document chunks.

        Args:
            chunks: List of dicts with 'text', 'source_material_id', 'source_title'
            max_cards: Maximum number of cards to generate

        Returns:
            List of dicts with 'question', 'answer', 'source_material_id'
        """
        # Format chunks for the prompt
        chunks_text = ""
        for i, chunk in enumerate(chunks[:20]):  # Limit to 20 chunks for context
            chunks_text += f"\n[Chunk {i+1} from '{chunk.get('source_title', 'Unknown')}']\n{chunk['text']}\n"

        system_prompt = """You are an expert at creating educational flashcards for spaced repetition learning.

Your task is to create high-quality flashcards from the provided document excerpts.

Rules for creating flashcards:
1. Each card should test ONE specific concept, fact, or idea
2. Questions should be clear and unambiguous
3. Answers should be concise but complete
4. Focus on the most important, memorable information
5. Avoid trivial or obvious questions
6. Use active recall principles - questions should require thinking, not just recognition
7. Include a mix of:
   - Definition cards (What is X?)
   - Concept cards (Explain how X works)
   - Application cards (When would you use X?)
   - Comparison cards (What's the difference between X and Y?)

Return your response as a JSON array of objects with this exact format:
[
  {"question": "...", "answer": "...", "chunk_index": N},
  ...
]

Where chunk_index is the 1-based index of the chunk the card was derived from.
Only return the JSON array, no other text."""

        user_prompt = f"""Create {max_cards} flashcards from these document excerpts:

{chunks_text}

Remember to return ONLY a valid JSON array."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        # Parse the JSON response
        response_text = response.content[0].text.strip()

        # Try to extract JSON from the response
        try:
            # First try direct parse
            cards_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON array in response
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                cards_data = json.loads(json_match.group())
            else:
                return []

        # Map chunk_index back to source_material_id
        result = []
        for card in cards_data:
            chunk_idx = card.get("chunk_index", 1) - 1  # Convert to 0-based
            source_material_id = None
            if 0 <= chunk_idx < len(chunks):
                source_material_id = chunks[chunk_idx].get("source_material_id")

            result.append({
                "question": card.get("question", ""),
                "answer": card.get("answer", ""),
                "source_material_id": source_material_id
            })

        return result[:max_cards]


llm_service = LLMService()
