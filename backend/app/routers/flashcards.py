from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models.flashcard import FlashcardDeck, Flashcard, CardReview
from app.models.notebook import Notebook
from app.models.user import User
from app.schemas.flashcard import (
    FlashcardDeckCreate, FlashcardDeckUpdate, FlashcardDeckResponse,
    FlashcardCreate, FlashcardUpdate, FlashcardResponse,
    CardReviewCreate, CardReviewResponse
)

router = APIRouter(tags=["flashcards"])


# Deck endpoints
@router.post("/decks", response_model=FlashcardDeckResponse, status_code=201)
def create_deck(deck: FlashcardDeckCreate, notebook_id: str, db: Session = Depends(get_db)):
    notebook = db.query(Notebook).filter(Notebook.id == notebook_id).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    db_deck = FlashcardDeck(**deck.model_dump(), notebook_id=notebook_id)
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    return db_deck


@router.get("/decks", response_model=List[FlashcardDeckResponse])
def list_decks(notebook_id: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(FlashcardDeck)
    if notebook_id:
        query = query.filter(FlashcardDeck.notebook_id == notebook_id)
    return query.offset(skip).limit(limit).all()


@router.get("/decks/{deck_id}", response_model=FlashcardDeckResponse)
def get_deck(deck_id: str, db: Session = Depends(get_db)):
    deck = db.query(FlashcardDeck).filter(FlashcardDeck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck


@router.patch("/decks/{deck_id}", response_model=FlashcardDeckResponse)
def update_deck(deck_id: str, deck_update: FlashcardDeckUpdate, db: Session = Depends(get_db)):
    deck = db.query(FlashcardDeck).filter(FlashcardDeck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    update_data = deck_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(deck, field, value)

    db.commit()
    db.refresh(deck)
    return deck


@router.delete("/decks/{deck_id}", status_code=204)
def delete_deck(deck_id: str, db: Session = Depends(get_db)):
    deck = db.query(FlashcardDeck).filter(FlashcardDeck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    db.delete(deck)
    db.commit()


# Flashcard endpoints
@router.post("/decks/{deck_id}/cards", response_model=FlashcardResponse, status_code=201)
def create_flashcard(deck_id: str, card: FlashcardCreate, db: Session = Depends(get_db)):
    deck = db.query(FlashcardDeck).filter(FlashcardDeck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    db_card = Flashcard(**card.model_dump(), deck_id=deck_id)
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card


@router.get("/decks/{deck_id}/cards", response_model=List[FlashcardResponse])
def list_flashcards(deck_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    deck = db.query(FlashcardDeck).filter(FlashcardDeck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    return db.query(Flashcard).filter(Flashcard.deck_id == deck_id).offset(skip).limit(limit).all()


@router.get("/cards/due", response_model=List[FlashcardResponse])
def get_due_cards(deck_id: str = None, limit: int = 20, db: Session = Depends(get_db)):
    """Get cards due for review (next_review_at <= now or null)"""
    now = datetime.now(timezone.utc)
    query = db.query(Flashcard).filter(
        (Flashcard.next_review_at <= now) | (Flashcard.next_review_at == None)
    )
    if deck_id:
        query = query.filter(Flashcard.deck_id == deck_id)
    return query.limit(limit).all()


@router.get("/cards/{card_id}", response_model=FlashcardResponse)
def get_flashcard(card_id: str, db: Session = Depends(get_db)):
    card = db.query(Flashcard).filter(Flashcard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    return card


@router.patch("/cards/{card_id}", response_model=FlashcardResponse)
def update_flashcard(card_id: str, card_update: FlashcardUpdate, db: Session = Depends(get_db)):
    card = db.query(Flashcard).filter(Flashcard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    update_data = card_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(card, field, value)

    db.commit()
    db.refresh(card)
    return card


@router.delete("/cards/{card_id}", status_code=204)
def delete_flashcard(card_id: str, db: Session = Depends(get_db)):
    card = db.query(Flashcard).filter(Flashcard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    db.delete(card)
    db.commit()


# Card review endpoints
@router.post("/cards/{card_id}/reviews", response_model=CardReviewResponse, status_code=201)
def create_card_review(card_id: str, review: CardReviewCreate, user_id: str, db: Session = Depends(get_db)):
    card = db.query(Flashcard).filter(Flashcard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_review = CardReview(**review.model_dump(), flashcard_id=card_id, user_id=user_id)
    db.add(db_review)

    # Update card SRS parameters (simplified SM-2 algorithm)
    quality = review.quality
    if quality >= 3:
        if card.interval_days == 1:
            card.interval_days = 6
        else:
            card.interval_days = int(card.interval_days * card.ease_factor)
    else:
        card.interval_days = 1

    card.ease_factor = max(1.3, card.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    card.next_review_at = datetime.now(timezone.utc) + timedelta(days=card.interval_days)

    db.commit()
    db.refresh(db_review)
    return db_review


@router.get("/cards/{card_id}/reviews", response_model=List[CardReviewResponse])
def list_card_reviews(card_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    card = db.query(Flashcard).filter(Flashcard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    return db.query(CardReview).filter(CardReview.flashcard_id == card_id).offset(skip).limit(limit).all()
