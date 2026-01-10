from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.notebook import NotebookCreate, NotebookUpdate, NotebookResponse
from app.schemas.source_material import SourceMaterialCreate, SourceMaterialUpdate, SourceMaterialResponse
from app.schemas.knowledge_node import KnowledgeNodeCreate, KnowledgeNodeUpdate, KnowledgeNodeResponse
from app.schemas.flashcard import (
    FlashcardDeckCreate, FlashcardDeckUpdate, FlashcardDeckResponse,
    FlashcardCreate, FlashcardUpdate, FlashcardResponse,
    CardReviewCreate, CardReviewResponse
)
from app.schemas.quiz import (
    QuizCreate, QuizUpdate, QuizResponse,
    QuizQuestionCreate, QuizQuestionUpdate, QuizQuestionResponse,
    QuizAttemptCreate, QuizAttemptUpdate, QuizAttemptResponse
)
from app.schemas.report import ReportCreate, ReportUpdate, ReportResponse

__all__ = [
    "UserCreate", "UserUpdate", "UserResponse",
    "NotebookCreate", "NotebookUpdate", "NotebookResponse",
    "SourceMaterialCreate", "SourceMaterialUpdate", "SourceMaterialResponse",
    "KnowledgeNodeCreate", "KnowledgeNodeUpdate", "KnowledgeNodeResponse",
    "FlashcardDeckCreate", "FlashcardDeckUpdate", "FlashcardDeckResponse",
    "FlashcardCreate", "FlashcardUpdate", "FlashcardResponse",
    "CardReviewCreate", "CardReviewResponse",
    "QuizCreate", "QuizUpdate", "QuizResponse",
    "QuizQuestionCreate", "QuizQuestionUpdate", "QuizQuestionResponse",
    "QuizAttemptCreate", "QuizAttemptUpdate", "QuizAttemptResponse",
    "ReportCreate", "ReportUpdate", "ReportResponse",
]
