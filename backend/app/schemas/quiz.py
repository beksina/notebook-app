from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any
from app.models.quiz import QuizType, QuestionType


class QuizBase(BaseModel):
    quiz_type: QuizType
    knowledge_node_ids: Optional[list[str]] = None
    scheduled_for: Optional[datetime] = None


class QuizCreate(QuizBase):
    pass


class QuizUpdate(BaseModel):
    quiz_type: Optional[QuizType] = None
    knowledge_node_ids: Optional[list[str]] = None
    scheduled_for: Optional[datetime] = None


class QuizResponse(QuizBase):
    id: str
    notebook_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QuizQuestionBase(BaseModel):
    question: str
    correct_answer: str
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    options: Optional[list[str]] = None
    knowledge_node_id: Optional[str] = None


class QuizQuestionCreate(QuizQuestionBase):
    pass


class QuizQuestionUpdate(BaseModel):
    question: Optional[str] = None
    correct_answer: Optional[str] = None
    question_type: Optional[QuestionType] = None
    options: Optional[list[str]] = None
    knowledge_node_id: Optional[str] = None


class QuizQuestionResponse(QuizQuestionBase):
    id: str
    quiz_id: str

    model_config = {"from_attributes": True}


class QuizAttemptBase(BaseModel):
    answers: Optional[dict[str, Any]] = None


class QuizAttemptCreate(QuizAttemptBase):
    pass


class QuizAttemptUpdate(BaseModel):
    score: Optional[float] = None
    answers: Optional[dict[str, Any]] = None
    completed_at: Optional[datetime] = None
    time_taken_minutes: Optional[int] = None


class QuizAttemptResponse(QuizAttemptBase):
    id: str
    quiz_id: str
    user_id: str
    score: Optional[float]
    completed_at: Optional[datetime]
    time_taken_minutes: Optional[int]

    model_config = {"from_attributes": True}
