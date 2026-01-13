"use client";

import { Highlight, HighlightColor } from "@/types/highlight";
import HighlightCard from "./HighlightCard";
import { MessageSquareText } from "lucide-react";

interface NotesSidebarProps {
  highlights: Highlight[];
  onHighlightClick: (highlight: Highlight) => void;
  onUpdateNote: (id: string, note: string) => void;
  onDeleteHighlight: (id: string) => void;
  onChangeColor: (id: string, color: HighlightColor) => void;
}

export default function NotesSidebar({
  highlights,
  onHighlightClick,
  onUpdateNote,
  onDeleteHighlight,
  onChangeColor,
}: NotesSidebarProps) {
  // Sort highlights by position (page for PDF, offset for text)
  const sortedHighlights = [...highlights].sort((a, b) => {
    // First sort by page if available
    if (a.position.page !== undefined && b.position.page !== undefined) {
      if (a.position.page !== b.position.page) {
        return a.position.page - b.position.page;
      }
    }
    // Then sort by offset
    const aOffset = a.position.start_offset ?? 0;
    const bOffset = b.position.start_offset ?? 0;
    return aOffset - bOffset;
  });

  return (
    <div className="w-72 h-full flex flex-col bg-white dark:bg-[#1c1c1b] border-l border-gray-200 dark:border-[#2a2a29]">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-[#2a2a29]">
        <div className="flex items-center gap-2">
          <MessageSquareText className="w-5 h-5 text-amber-500" />
          <h3 className="font-semibold text-gray-900 dark:text-white">
            Notes & Highlights
          </h3>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {highlights.length} highlight{highlights.length !== 1 ? "s" : ""}
        </p>
      </div>

      {/* Highlights list */}
      <div className="flex-1 overflow-y-auto divide-y divide-gray-100 dark:divide-[#2a2a29]">
        {sortedHighlights.map((highlight) => (
          <HighlightCard
            key={highlight.id}
            highlight={highlight}
            onClick={() => onHighlightClick(highlight)}
            onUpdateNote={(note) => onUpdateNote(highlight.id, note)}
            onDelete={() => onDeleteHighlight(highlight.id)}
            onChangeColor={(color) => onChangeColor(highlight.id, color)}
          />
        ))}
      </div>

      {/* Empty state */}
      {highlights.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
          <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-[#242423] flex items-center justify-center mb-3">
            <MessageSquareText className="w-6 h-6 text-gray-400" />
          </div>
          <p className="text-gray-500 dark:text-gray-400 font-medium">
            No highlights yet
          </p>
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
            Select text to create a highlight
          </p>
        </div>
      )}
    </div>
  );
}
