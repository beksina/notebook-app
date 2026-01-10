"""Application configuration settings."""

from pathlib import Path
import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Storage
    UPLOAD_DIR: Path = Path("./uploads")
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: set = {".pdf", ".txt", ".md", ".docx"}

    # ChromaDB
    CHROMA_PERSIST_DIR: Path = Path("./chroma_db")
    CHROMA_COLLECTION_NAME: str = "recall_pro_documents"

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Anthropic
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    # ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"

    # Chunking
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
