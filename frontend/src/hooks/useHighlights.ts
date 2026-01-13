"use client";

import { useState, useEffect, useCallback } from "react";
import { useApi } from "./useApi";
import { Highlight, HighlightCreate, HighlightUpdate } from "@/types/highlight";

export function useHighlights(notebookId: string, materialId: string) {
  const { api, isAuthenticated } = useApi();
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const basePath = `/api/notebooks/${notebookId}/materials/${materialId}/highlights`;

  const fetchHighlights = useCallback(async () => {
    if (!isAuthenticated) return;

    try {
      setIsLoading(true);
      const data = await api.get<Highlight[]>(basePath);
      setHighlights(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch highlights");
    } finally {
      setIsLoading(false);
    }
  }, [api, basePath, isAuthenticated]);

  useEffect(() => {
    fetchHighlights();
  }, [fetchHighlights]);

  const createHighlight = async (highlight: HighlightCreate): Promise<Highlight> => {
    const newHighlight = await api.post<Highlight>(basePath, highlight);
    setHighlights((prev) => [...prev, newHighlight]);
    return newHighlight;
  };

  const updateHighlight = async (id: string, update: HighlightUpdate): Promise<Highlight> => {
    const updated = await api.patch<Highlight>(`${basePath}/${id}`, update);
    setHighlights((prev) => prev.map((h) => (h.id === id ? updated : h)));
    return updated;
  };

  const deleteHighlight = async (id: string): Promise<void> => {
    await api.delete(`${basePath}/${id}`);
    setHighlights((prev) => prev.filter((h) => h.id !== id));
  };

  return {
    highlights,
    isLoading,
    error,
    createHighlight,
    updateHighlight,
    deleteHighlight,
    refetch: fetchHighlights,
  };
}
