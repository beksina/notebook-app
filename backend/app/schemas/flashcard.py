from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.flashcard import Difficulty, CardType


class FlashcardDeckBase(BaseModel):
    title: str


class FlashcardDeckCreate(FlashcardDeckBase):
    pass


class FlashcardDeckUpdate(BaseModel):
    title: Optional[str] = None


class FlashcardDeckResponse(FlashcardDeckBase):
    id: str
    notebook_id: str
    created_at: datetime
    card_count: int = 0

    model_config = {"from_attributes": True}


class FlashcardBase(BaseModel):
    question: str
    answer: str
    difficulty: Difficulty = Difficulty.MEDIUM
    card_type: CardType = CardType.BASIC
    knowledge_node_id: Optional[str] = None
    source_material_id: Optional[str] = None


class FlashcardCreate(FlashcardBase):
    pass


class FlashcardUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    difficulty: Optional[Difficulty] = None
    card_type: Optional[CardType] = None
    knowledge_node_id: Optional[str] = None
    source_material_id: Optional[str] = None
    next_review_at: Optional[datetime] = None
    interval_days: Optional[int] = None
    ease_factor: Optional[float] = None


class FlashcardResponse(FlashcardBase):
    id: str
    deck_id: str
    created_at: datetime
    next_review_at: Optional[datetime]
    interval_days: int
    ease_factor: float
    source_material_id: Optional[str] = None

    model_config = {"from_attributes": True}


class CardReviewBase(BaseModel):
    quality: int  # 1-5 rating
    time_taken_seconds: Optional[int] = None


class CardReviewCreate(CardReviewBase):
    pass


class CardReviewResponse(CardReviewBase):
    id: str
    flashcard_id: str
    user_id: str
    reviewed_at: datetime

    model_config = {"from_attributes": True}


# Card generation schemas
class GenerateCardsRequest(BaseModel):
    source_material_ids: Optional[list[str]] = None  # None means all materials
    max_cards: int = 10


class GeneratedCard(BaseModel):
    question: str
    answer: str
    source_material_id: Optional[str] = None
