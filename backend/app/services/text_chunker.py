"""Text chunking service for splitting documents into embeddable chunks."""

from typing import List
import re

import tiktoken

from app.core.config import settings


class TextChunker:
    """Split text into chunks suitable for embedding."""

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
        encoding_name: str = "cl100k_base"  # Used by text-embedding-3-small
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks based on token count.
        Uses sentence boundaries when possible.
        """
        if not text.strip():
            return []

        # Split into sentences first
        sentences = self._split_into_sentences(text)

        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = len(self.encoding.encode(sentence))

            # If single sentence exceeds chunk size, split it
            if sentence_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0

                # Split long sentence into smaller pieces
                chunks.extend(self._split_long_sentence(sentence))
                continue

            # If adding this sentence would exceed chunk size
            if current_tokens + sentence_tokens > self.chunk_size:
                # Save current chunk
                chunks.append(" ".join(current_chunk))

                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk, self.chunk_overlap
                )
                current_chunk = overlap_sentences + [sentence]
                current_tokens = sum(
                    len(self.encoding.encode(s)) for s in current_chunk
                )
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Simple sentence splitting."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _split_long_sentence(self, sentence: str) -> List[str]:
        """Split a sentence that's too long for a single chunk."""
        words = sentence.split()
        chunks = []
        current = []
        current_tokens = 0

        for word in words:
            word_tokens = len(self.encoding.encode(word + " "))
            if current_tokens + word_tokens > self.chunk_size:
                if current:
                    chunks.append(" ".join(current))
                current = [word]
                current_tokens = word_tokens
            else:
                current.append(word)
                current_tokens += word_tokens

        if current:
            chunks.append(" ".join(current))

        return chunks

    def _get_overlap_sentences(
        self, sentences: List[str], target_tokens: int
    ) -> List[str]:
        """Get sentences from the end that fit within overlap token count."""
        overlap = []
        tokens = 0

        for sentence in reversed(sentences):
            sentence_tokens = len(self.encoding.encode(sentence))
            if tokens + sentence_tokens <= target_tokens:
                overlap.insert(0, sentence)
                tokens += sentence_tokens
            else:
                break

        return overlap


# Singleton
text_chunker = TextChunker()
