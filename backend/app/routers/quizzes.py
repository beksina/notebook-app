from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt
from app.models.notebook import Notebook
from app.models.user import User
from app.schemas.quiz import (
    QuizCreate, QuizUpdate, QuizResponse,
    QuizQuestionCreate, QuizQuestionUpdate, QuizQuestionResponse,
    QuizAttemptCreate, QuizAttemptUpdate, QuizAttemptResponse
)

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


# Quiz endpoints
@router.post("/", response_model=QuizResponse, status_code=201)
def create_quiz(quiz: QuizCreate, notebook_id: str, db: Session = Depends(get_db)):
    notebook = db.query(Notebook).filter(Notebook.id == notebook_id).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    db_quiz = Quiz(**quiz.model_dump(), notebook_id=notebook_id)
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    return db_quiz


@router.get("/", response_model=List[QuizResponse])
def list_quizzes(notebook_id: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(Quiz)
    if notebook_id:
        query = query.filter(Quiz.notebook_id == notebook_id)
    return query.offset(skip).limit(limit).all()


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: str, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@router.patch("/{quiz_id}", response_model=QuizResponse)
def update_quiz(quiz_id: str, quiz_update: QuizUpdate, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    update_data = quiz_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(quiz, field, value)

    db.commit()
    db.refresh(quiz)
    return quiz


@router.delete("/{quiz_id}", status_code=204)
def delete_quiz(quiz_id: str, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    db.delete(quiz)
    db.commit()


# Quiz question endpoints
@router.post("/{quiz_id}/questions", response_model=QuizQuestionResponse, status_code=201)
def create_quiz_question(quiz_id: str, question: QuizQuestionCreate, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    db_question = QuizQuestion(**question.model_dump(), quiz_id=quiz_id)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


@router.get("/{quiz_id}/questions", response_model=List[QuizQuestionResponse])
def list_quiz_questions(quiz_id: str, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    return db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).all()


@router.get("/questions/{question_id}", response_model=QuizQuestionResponse)
def get_quiz_question(question_id: str, db: Session = Depends(get_db)):
    question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.patch("/questions/{question_id}", response_model=QuizQuestionResponse)
def update_quiz_question(question_id: str, question_update: QuizQuestionUpdate, db: Session = Depends(get_db)):
    question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    update_data = question_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)
    return question


@router.delete("/questions/{question_id}", status_code=204)
def delete_quiz_question(question_id: str, db: Session = Depends(get_db)):
    question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    db.delete(question)
    db.commit()


# Quiz attempt endpoints
@router.post("/{quiz_id}/attempts", response_model=QuizAttemptResponse, status_code=201)
def create_quiz_attempt(quiz_id: str, attempt: QuizAttemptCreate, user_id: str, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_attempt = QuizAttempt(**attempt.model_dump(), quiz_id=quiz_id, user_id=user_id)
    db.add(db_attempt)
    db.commit()
    db.refresh(db_attempt)
    return db_attempt


@router.get("/{quiz_id}/attempts", response_model=List[QuizAttemptResponse])
def list_quiz_attempts(quiz_id: str, user_id: str = None, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    query = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz_id)
    if user_id:
        query = query.filter(QuizAttempt.user_id == user_id)
    return query.all()


@router.get("/attempts/{attempt_id}", response_model=QuizAttemptResponse)
def get_quiz_attempt(attempt_id: str, db: Session = Depends(get_db)):
    attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return attempt


@router.patch("/attempts/{attempt_id}", response_model=QuizAttemptResponse)
def update_quiz_attempt(attempt_id: str, attempt_update: QuizAttemptUpdate, db: Session = Depends(get_db)):
    attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    update_data = attempt_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(attempt, field, value)

    db.commit()
    db.refresh(attempt)
    return attempt
