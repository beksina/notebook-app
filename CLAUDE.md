# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

Recall Pro is a learning application with a Next.js frontend and FastAPI backend. It enables users to upload study materials (PDFs, documents, markdown), organize them into notebooks, and generate flashcards and quizzes using AI.

## Architecture

```
recall-pro/
├── frontend/          # Next.js 16 with React 19, TypeScript, Tailwind v4
│   └── src/
│       ├── app/       # App Router pages
│       ├── components/# React components (viewers, highlights, chat)
│       ├── hooks/     # Custom hooks (useApi, useHighlights)
│       ├── lib/       # API client utilities
│       └── types/     # TypeScript type definitions
│
└── backend/           # FastAPI with SQLAlchemy, ChromaDB
    └── app/
        ├── core/      # Configuration (settings, constants)
        ├── models/    # SQLAlchemy ORM models
        ├── routers/   # API route handlers
        ├── schemas/   # Pydantic request/response schemas
        └── services/  # Business logic (LLM, embeddings, document processing)
```

## Development Commands

### Frontend (from `frontend/` directory)
```bash
npm run dev      # Start development server (port 3000)
npm run build    # Production build
npm run lint     # Run ESLint
```

### Backend (from `backend/` directory)
```bash
# Using virtual environment
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run server
uvicorn main:app --reload    # or: ./run.sh
```

## Key Technologies

**Frontend:**
- Next.js 16.1 with App Router
- React 19 with TypeScript
- Tailwind CSS v4
- NextAuth v5 (beta) for authentication
- react-pdf for PDF viewing
- mammoth for DOCX conversion

**Backend:**
- FastAPI with async support
- SQLAlchemy ORM with SQLite (default)
- ChromaDB for vector storage
- OpenAI embeddings (text-embedding-3-small)
- Anthropic Claude for AI features (claude-sonnet-4-20250514)
- Pydantic v2 for validation

## Environment Variables

### Backend (`backend/.env`)
```
FRONTEND_URL=http://localhost:3000
DATABASE_URL=sqlite:///./recall_pro.db
JWT_SECRET_KEY=<your-secret>
OPENAI_API_KEY=<for-embeddings>
ANTHROPIC_API_KEY=<for-chat-and-generation>
```

## API Structure

All backend routes are prefixed with `/api`:
- `/api/auth` - Authentication (login, register)
- `/api/users` - User management
- `/api/notebooks` - Notebook CRUD and source materials
- `/api/flashcards` - Flashcard decks and cards
- `/api/quizzes` - Quiz generation and attempts
- `/api/reports` - Learning reports

## Data Models

Core entities: `User`, `Notebook`, `SourceMaterial`, `KnowledgeNode`, `FlashcardDeck`, `Flashcard`, `CardReview`, `Quiz`, `QuizQuestion`, `QuizAttempt`, `Report`, `Highlight`

## File Upload

Supported formats: `.pdf`, `.txt`, `.md`, `.docx`
Max file size: 10MB (configurable in `backend/app/core/config.py`)

## Code Patterns

- Frontend uses custom `useApi` hook for authenticated API calls
- Backend services handle business logic, routers handle HTTP concerns
- Pydantic schemas separate request/response shapes from ORM models
- Document processing: upload → chunk → embed → store in ChromaDB
