from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

load_dotenv()

from app.database import engine, Base
from app.routers import auth, users, notebooks, flashcards, quizzes, reports

# Import all models to register them with Base
from app.models import (
    User, Notebook, SourceMaterial, KnowledgeNode,
    FlashcardDeck, Flashcard, CardReview,
    Quiz, QuizQuestion, QuizAttempt, Report
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    Base.metadata.create_all(bind=engine)

    # Ensure upload and ChromaDB directories exist
    from app.core.config import settings
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

    yield


app = FastAPI(
    title="Recall Pro API",
    description="Backend API for the ultimate learning app",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(notebooks.router, prefix="/api")
app.include_router(flashcards.router, prefix="/api")
app.include_router(quizzes.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Welcome to Recall Pro API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
