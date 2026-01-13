"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Plus,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Trash2,
  Loader2,
  Layers,
  Pencil,
  X,
  Check,
  Clock,
  RotateCcw,
} from "lucide-react";
import { useApi } from "@/hooks/useApi";
import { SSEEvent } from "@/lib/api";

interface Deck {
  id: string;
  title: string;
  notebook_id: string;
  created_at: string;
  card_count: number;
}

interface Card {
  id: string;
  question: string;
  answer: string;
  deck_id: string;
  source_material_id?: string;
  next_review_at?: string;
  interval_days: number;
  ease_factor: number;
}

interface DecksViewProps {
  notebookId: string;
}

export default function DecksView({ notebookId }: DecksViewProps) {
  const { api, isAuthenticated } = useApi();
  const [decks, setDecks] = useState<Deck[]>([]);
  const [selectedDeck, setSelectedDeck] = useState<Deck | null>(null);
  const [cards, setCards] = useState<Card[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreatingDeck, setIsCreatingDeck] = useState(false);
  const [newDeckTitle, setNewDeckTitle] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState("");
  const [isFlipped, setIsFlipped] = useState(false);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [showReviewButtons, setShowReviewButtons] = useState(false);
  const [isReviewing, setIsReviewing] = useState(false);

  // Edit state
  const [editingCard, setEditingCard] = useState<Card | null>(null);
  const [editQuestion, setEditQuestion] = useState("");
  const [editAnswer, setEditAnswer] = useState("");
  const [isSavingEdit, setIsSavingEdit] = useState(false);

  // Helper to check if card is due
  const isDue = (card: Card) => {
    if (!card.next_review_at) return true;
    return new Date(card.next_review_at) <= new Date();
  };

  // Get due cards count
  const dueCardsCount = cards.filter(isDue).length;

  // Format next review date
  const formatNextReview = (card: Card) => {
    if (!card.next_review_at) return "New card";
    const date = new Date(card.next_review_at);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays <= 0) return "Due now";
    if (diffDays === 1) return "Due tomorrow";
    if (diffDays < 7) return `Due in ${diffDays} days`;
    if (diffDays < 30) return `Due in ${Math.ceil(diffDays / 7)} weeks`;
    return `Due in ${Math.ceil(diffDays / 30)} months`;
  };

  // Keyboard shortcuts for card navigation
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!selectedDeck || cards.length === 0) return;
      if (editingCard) return; // Don't handle keys while editing

      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      switch (e.code) {
        case "Space":
          e.preventDefault();
          if (!isFlipped) {
            setIsFlipped(true);
            setShowReviewButtons(true);
          } else {
            setIsFlipped(false);
            setShowReviewButtons(false);
          }
          break;
        case "ArrowLeft":
          e.preventDefault();
          goToCard(Math.max(0, currentCardIndex - 1));
          break;
        case "ArrowRight":
          e.preventDefault();
          goToCard(Math.min(cards.length - 1, currentCardIndex + 1));
          break;
        case "Digit1":
        case "Numpad1":
          if (showReviewButtons) {
            e.preventDefault();
            handleReview(1);
          }
          break;
        case "Digit2":
        case "Numpad2":
          if (showReviewButtons) {
            e.preventDefault();
            handleReview(3);
          }
          break;
        case "Digit3":
        case "Numpad3":
          if (showReviewButtons) {
            e.preventDefault();
            handleReview(5);
          }
          break;
      }
    },
    [selectedDeck, cards.length, currentCardIndex, isFlipped, showReviewButtons, editingCard]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  // Fetch decks
  useEffect(() => {
    const fetchDecks = async () => {
      if (!isAuthenticated) return;
      setIsLoading(true);
      try {
        const data = (await api.get(
          `/api/notebooks/${notebookId}/decks`
        )) as Deck[];
        setDecks(data);
      } catch (e) {
        console.error("Failed to fetch decks:", e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchDecks();
  }, [isAuthenticated, notebookId]);

  // Fetch cards when deck is selected
  useEffect(() => {
    const fetchCards = async () => {
      if (!selectedDeck || !isAuthenticated) return;
      setIsLoading(true);
      try {
        const data = (await api.get(
          `/api/notebooks/${notebookId}/decks/${selectedDeck.id}/cards`
        )) as Card[];
        setCards(data);
        setCurrentCardIndex(0);
        setIsFlipped(false);
        setShowReviewButtons(false);
      } catch (e) {
        console.error("Failed to fetch cards:", e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchCards();
  }, [selectedDeck, isAuthenticated, notebookId]);

  const handleCreateDeck = async () => {
    if (!newDeckTitle.trim()) return;
    try {
      const deck = (await api.post(`/api/notebooks/${notebookId}/decks`, {
        title: newDeckTitle.trim(),
      })) as Deck;
      setDecks((prev) => [...prev, deck]);
      setNewDeckTitle("");
      setIsCreatingDeck(false);
    } catch (e) {
      console.error("Failed to create deck:", e);
    }
  };

  const handleDeleteDeck = async (deckId: string) => {
    if (!confirm("Delete this deck and all its cards?")) return;
    try {
      await api.delete(`/api/notebooks/${notebookId}/decks/${deckId}`);
      setDecks((prev) => prev.filter((d) => d.id !== deckId));
      if (selectedDeck?.id === deckId) {
        setSelectedDeck(null);
        setCards([]);
      }
    } catch (e) {
      console.error("Failed to delete deck:", e);
    }
  };

  const handleGenerateCards = async () => {
    if (!selectedDeck) return;
    setIsGenerating(true);
    setGenerationStatus("Starting generation...");

    api.streamPost(
      `/api/notebooks/${notebookId}/decks/${selectedDeck.id}/generate`,
      { max_cards: 10 },
      (event: SSEEvent) => {
        switch (event.event.trim()) {
          case "status":
            setGenerationStatus(event.data.message as string);
            break;
          case "card":
            const newCard: Card = {
              id: event.data.id as string,
              question: event.data.question as string,
              answer: event.data.answer as string,
              deck_id: selectedDeck.id,
              source_material_id: event.data.source_material_id as string | undefined,
              interval_days: 1,
              ease_factor: 2.5,
            };
            setCards((prev) => [...prev, newCard]);
            setDecks((prev) =>
              prev.map((d) =>
                d.id === selectedDeck.id
                  ? { ...d, card_count: d.card_count + 1 }
                  : d
              )
            );
            setSelectedDeck((prev) =>
              prev ? { ...prev, card_count: prev.card_count + 1 } : prev
            );
            break;
          case "done":
            setIsGenerating(false);
            setGenerationStatus("");
            break;
          case "error":
            setIsGenerating(false);
            setGenerationStatus(`Error: ${event.data.message}`);
            setTimeout(() => setGenerationStatus(""), 3000);
            break;
        }
      }
    );
  };

  const handleDeleteCard = async (cardId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.delete(`/api/notebooks/${notebookId}/cards/${cardId}`);
      setCards((prev) => {
        const newCards = prev.filter((c) => c.id !== cardId);
        if (currentCardIndex >= newCards.length && newCards.length > 0) {
          setCurrentCardIndex(newCards.length - 1);
        }
        return newCards;
      });
      setDecks((prev) =>
        prev.map((d) =>
          d.id === selectedDeck?.id ? { ...d, card_count: d.card_count - 1 } : d
        )
      );
      if (selectedDeck) {
        setSelectedDeck((prev) =>
          prev ? { ...prev, card_count: prev.card_count - 1 } : prev
        );
      }
    } catch (e) {
      console.error("Failed to delete card:", e);
    }
  };

  const goToCard = (index: number) => {
    setCurrentCardIndex(index);
    setIsFlipped(false);
    setShowReviewButtons(false);
  };

  const handleFlip = () => {
    if (!isFlipped) {
      setIsFlipped(true);
      setShowReviewButtons(true);
    } else {
      setIsFlipped(false);
      setShowReviewButtons(false);
    }
  };

  // Review handler with spaced repetition
  const handleReview = async (quality: number) => {
    if (!cards[currentCardIndex] || isReviewing) return;

    setIsReviewing(true);
    const card = cards[currentCardIndex];

    try {
      await api.post(`/api/notebooks/${notebookId}/cards/${card.id}/review`, {
        quality,
      });

      // Fetch updated card to get new interval
      const updatedCard = (await api.get(
        `/api/notebooks/${notebookId}/cards/${card.id}`
      )) as Card;

      // Update local state
      setCards((prev) =>
        prev.map((c) => (c.id === card.id ? updatedCard : c))
      );

      // Move to next card
      if (currentCardIndex < cards.length - 1) {
        goToCard(currentCardIndex + 1);
      } else {
        // Loop back to first card or show completion
        setIsFlipped(false);
        setShowReviewButtons(false);
      }
    } catch (e) {
      console.error("Failed to record review:", e);
    } finally {
      setIsReviewing(false);
    }
  };

  // Edit handlers
  const startEditing = (card: Card, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingCard(card);
    setEditQuestion(card.question);
    setEditAnswer(card.answer);
  };

  const cancelEditing = () => {
    setEditingCard(null);
    setEditQuestion("");
    setEditAnswer("");
  };

  const saveEdit = async () => {
    if (!editingCard || !editQuestion.trim() || !editAnswer.trim()) return;

    setIsSavingEdit(true);
    try {
      const updated = (await api.patch(
        `/api/notebooks/${notebookId}/cards/${editingCard.id}`,
        {
          question: editQuestion.trim(),
          answer: editAnswer.trim(),
        }
      )) as Card;

      setCards((prev) =>
        prev.map((c) => (c.id === editingCard.id ? updated : c))
      );
      cancelEditing();
    } catch (e) {
      console.error("Failed to update card:", e);
    } finally {
      setIsSavingEdit(false);
    }
  };

  // Deck list view
  if (!selectedDeck) {
    return (
      <div className="h-full flex flex-col bg-white dark:bg-[#1c1c1b] rounded-xl border border-gray-200 dark:border-[#2a2a29] overflow-hidden">
        <div className="flex-shrink-0 p-4 border-b border-gray-200 dark:border-[#2a2a29]">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Card Decks
            </h2>
            <button
              onClick={() => setIsCreatingDeck(true)}
              className="flex items-center gap-2 px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-sm rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Deck
            </button>
          </div>

          {isCreatingDeck && (
            <div className="mt-4 flex gap-2">
              <input
                type="text"
                value={newDeckTitle}
                onChange={(e) => setNewDeckTitle(e.target.value)}
                placeholder="Deck name..."
                className="flex-1 min-w-0 px-3 py-2 rounded-lg border border-gray-300 dark:border-[#333332] bg-gray-50 dark:bg-[#242423] text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleCreateDeck();
                  if (e.key === "Escape") {
                    setIsCreatingDeck(false);
                    setNewDeckTitle("");
                  }
                }}
              />
              <button
                onClick={handleCreateDeck}
                className="flex-shrink-0 px-3 py-2 bg-amber-600 hover:bg-amber-700 text-white text-sm rounded-lg transition-colors"
              >
                Create
              </button>
              <button
                onClick={() => {
                  setIsCreatingDeck(false);
                  setNewDeckTitle("");
                }}
                className="flex-shrink-0 px-3 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white text-sm transition-colors"
              >
                Cancel
              </button>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="w-6 h-6 text-amber-600 animate-spin" />
            </div>
          ) : decks.length === 0 ? (
            <div className="text-center py-12">
              <Layers className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">
                No decks yet. Create one to get started!
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {decks.map((deck) => (
                <div
                  key={deck.id}
                  onClick={() => setSelectedDeck(deck)}
                  className="group relative p-4 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-[#2a2a29] dark:to-[#242423] rounded-xl border border-amber-200/50 dark:border-amber-900/30 hover:border-amber-300 dark:hover:border-amber-800 cursor-pointer transition-all hover:shadow-md"
                >
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteDeck(deck.id);
                    }}
                    className="absolute top-2 right-2 p-1.5 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all rounded-md hover:bg-white/50 dark:hover:bg-black/20"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <h3 className="font-medium text-gray-900 dark:text-white mb-1 pr-6">
                    {deck.title}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {deck.card_count} card{deck.card_count !== 1 ? "s" : ""}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Cards view for selected deck
  return (
    <div className="h-full flex flex-col bg-white dark:bg-[#1c1c1b] rounded-xl border border-gray-200 dark:border-[#2a2a29] overflow-hidden">
      {/* Edit Modal */}
      {editingCard && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-[#1c1c1b] rounded-xl p-6 w-full max-w-lg border border-gray-200 dark:border-[#2a2a29]">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Edit Card
              </h3>
              <button
                onClick={cancelEditing}
                className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Question (Front)
                </label>
                <textarea
                  value={editQuestion}
                  onChange={(e) => setEditQuestion(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-[#333332] bg-gray-50 dark:bg-[#242423] text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 resize-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Answer (Back)
                </label>
                <textarea
                  value={editAnswer}
                  onChange={(e) => setEditAnswer(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-[#333332] bg-gray-50 dark:bg-[#242423] text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 resize-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={cancelEditing}
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white text-sm transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={saveEdit}
                disabled={isSavingEdit || !editQuestion.trim() || !editAnswer.trim()}
                className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-700 disabled:bg-amber-600/50 disabled:cursor-not-allowed text-white text-sm rounded-lg transition-colors"
              >
                {isSavingEdit ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Check className="w-4 h-4" />
                )}
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-gray-200 dark:border-[#2a2a29]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => {
                setSelectedDeck(null);
                setCards([]);
              }}
              className="flex-shrink-0 p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-[#242423] transition-colors"
            >
              <ChevronLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
            <div className="min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                {selectedDeck.title}
              </h2>
              <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                <span>{cards.length} cards</span>
                {dueCardsCount > 0 && (
                  <span className="flex items-center gap-1 text-amber-600 dark:text-amber-500">
                    <Clock className="w-3 h-3" />
                    {dueCardsCount} due
                  </span>
                )}
              </div>
            </div>
          </div>

          <button
            onClick={handleGenerateCards}
            disabled={isGenerating}
            className="flex-shrink-0 flex items-center gap-2 px-3 py-1.5 bg-amber-600 hover:bg-amber-700 disabled:bg-amber-600/50 disabled:cursor-not-allowed text-white text-sm rounded-lg transition-colors"
          >
            {isGenerating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            <span className="hidden sm:inline">Generate</span>
          </button>
        </div>

        {generationStatus && (
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400 italic truncate">
            {generationStatus}
          </p>
        )}
      </div>

      {/* Cards area */}
      <div className="flex-1 overflow-y-auto p-4 min-h-0">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="w-6 h-6 text-amber-600 animate-spin" />
          </div>
        ) : cards.length === 0 ? (
          <div className="text-center py-12">
            <Layers className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              No cards in this deck yet.
            </p>
            <button
              onClick={handleGenerateCards}
              disabled={isGenerating}
              className="inline-flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition-colors"
            >
              <Sparkles className="w-4 h-4" />
              Generate from Documents
            </button>
          </div>
        ) : (
          <div className="flex flex-col h-full">
            {/* Study card */}
            <div className="flex-shrink-0 mb-6">
              {/* Card counter and status */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    Card {currentCardIndex + 1} of {cards.length}
                  </span>
                  <span className="text-xs text-gray-400 dark:text-gray-500 px-2 py-0.5 bg-gray-100 dark:bg-[#242423] rounded">
                    {formatNextReview(cards[currentCardIndex])}
                  </span>
                </div>
                <button
                  onClick={(e) => startEditing(cards[currentCardIndex], e)}
                  className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-[#242423] transition-colors"
                >
                  <Pencil className="w-4 h-4" />
                </button>
              </div>

              {/* Flashcard */}
              <div
                onClick={handleFlip}
                className={`relative h-52 rounded-xl border cursor-pointer transition-all hover:shadow-lg select-none ${
                  isDue(cards[currentCardIndex])
                    ? "bg-gradient-to-br from-amber-50 to-orange-50 dark:from-[#2a2a29] dark:to-[#242423] border-amber-200 dark:border-amber-900/30"
                    : "bg-gradient-to-br from-gray-50 to-gray-100 dark:from-[#252525] dark:to-[#1f1f1f] border-gray-200 dark:border-[#333]"
                }`}
              >
                <div className="absolute inset-0 flex items-center justify-center p-6 overflow-auto">
                  <div className="text-center max-w-full">
                    <p className="text-sm text-amber-600 dark:text-amber-500 mb-3 uppercase tracking-wide font-medium">
                      {isFlipped ? "Answer" : "Question"}
                    </p>
                    <p className="text-gray-900 dark:text-white break-words text-[16px]">
                      {isFlipped
                        ? cards[currentCardIndex].answer
                        : cards[currentCardIndex].question}
                    </p>
                  </div>
                </div>
                {!showReviewButtons && (
                  <p className="absolute bottom-3 left-0 right-0 text-center text-xs text-gray-400">
                    Click or press Space to flip
                  </p>
                )}
              </div>

              {/* Review buttons - shown after flipping */}
              {showReviewButtons && (
                <div className="mt-4">
                  {/* <p className="text-center text-xs text-gray-500 dark:text-gray-400 mb-3">
                    How well did you remember?
                  </p> */}
                  <div className="flex justify-center gap-2">
                    <button
                      onClick={() => handleReview(1)}
                      disabled={isReviewing}
                      className="flex-1 max-w-[120px] px-4 py-2.5 bg-red-100 dark:bg-red-900/30 hover:bg-red-200 dark:hover:bg-red-900/50 text-red-700 dark:text-red-400 text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                    >
                      <span className="block">Forgot</span>
                      {/* <span className="text-xs opacity-70">1 day</span> */}
                    </button>
                    <button
                      onClick={() => handleReview(3)}
                      disabled={isReviewing}
                      className="flex-1 max-w-[120px] px-4 py-2.5 bg-yellow-100 dark:bg-yellow-900/30 hover:bg-yellow-200 dark:hover:bg-yellow-900/50 text-yellow-700 dark:text-yellow-400 text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                    >
                      <span className="block">Hard</span>
                      <span className="text-xs opacity-70">
                        {/* {cards[currentCardIndex].interval_days === 1
                          ? "6 days"
                          : `${Math.round(cards[currentCardIndex].interval_days * 1.3)} days`} */}
                      </span>
                    </button>
                    <button
                      onClick={() => handleReview(5)}
                      disabled={isReviewing}
                      className="flex-1 max-w-[120px] px-4 py-2.5 bg-green-100 dark:bg-green-900/30 hover:bg-green-200 dark:hover:bg-green-900/50 text-green-700 dark:text-green-400 text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                    >
                      <span className="block">Easy</span>
                      <span className="text-xs opacity-70">
                        {/* {cards[currentCardIndex].interval_days === 1
                          ? "6 days"
                          : `${Math.round(cards[currentCardIndex].interval_days * cards[currentCardIndex].ease_factor)} days`} */}
                      </span>
                    </button>
                  </div>
                  <p className="text-center text-xs text-gray-400 mt-2">
                    Press 1, 2, or 3 for quick rating
                  </p>
                </div>
              )}

              {/* Navigation buttons - only show when not reviewing */}
              {!showReviewButtons && (
                <div className="flex items-center justify-center gap-4 mt-4">
                  <button
                    onClick={() => goToCard(Math.max(0, currentCardIndex - 1))}
                    disabled={currentCardIndex === 0}
                    className="flex items-center gap-1 px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    Previous
                  </button>
                  <button
                    onClick={() =>
                      goToCard(Math.min(cards.length - 1, currentCardIndex + 1))
                    }
                    disabled={currentCardIndex === cards.length - 1}
                    className="flex items-center gap-1 px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    Next
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            {/* Cards grid */}
            <div className="flex-1 min-h-0 border-t border-gray-200 dark:border-[#2a2a29] pt-4">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                All Cards
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 overflow-y-auto max-h-64">
                {cards.map((card, index) => (
                  <div
                    key={card.id}
                    onClick={() => goToCard(index)}
                    className={`group relative p-3 rounded-lg cursor-pointer transition-all ${
                      index === currentCardIndex
                        ? "bg-amber-100 dark:bg-amber-900/30 border-2 border-amber-400 dark:border-amber-700"
                        : isDue(card)
                        ? "bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-900/30 hover:border-amber-300 dark:hover:border-amber-800"
                        : "bg-gray-50 dark:bg-[#242423] border border-gray-200 dark:border-[#333] hover:border-gray-300 dark:hover:border-[#444]"
                    }`}
                  >
                    <div className="absolute top-1 right-1 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
                      <button
                        onClick={(e) => startEditing(card, e)}
                        className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                      >
                        <Pencil className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => handleDeleteCard(card.id, e)}
                        className="p-1 text-gray-400 hover:text-red-500"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                    <p className="text-md text-gray-900 dark:text-white line-clamp-2 pr-8">
                      {card.question}
                    </p>
                    {isDue(card) && (
                      <div className="flex items-center gap-1 mt-1.5 text-amber-600 dark:text-amber-500">
                        <Clock className="w-3 h-3" />
                        <span className="text-[12px]">Due</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
