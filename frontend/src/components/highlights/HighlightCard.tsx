"use client";

import { useState } from "react";
import { Trash2, Edit2, Check, X } from "lucide-react";
import { Highlight, HighlightColor } from "@/types/highlight";

interface HighlightCardProps {
  highlight: Highlight;
  onClick: () => void;
  onUpdateNote: (note: string) => void;
  onDelete: () => void;
  onChangeColor: (color: HighlightColor) => void;
}

const colorStyles: Record<HighlightColor, { border: string; bg: string }> = {
  yellow: { border: "border-l-yellow-400", bg: "bg-yellow-300" },
  green: { border: "border-l-green-400", bg: "bg-green-300" },
  blue: { border: "border-l-blue-400", bg: "bg-blue-300" },
  pink: { border: "border-l-pink-400", bg: "bg-pink-300" },
};

const colors: HighlightColor[] = ["yellow", "green", "blue", "pink"];

export default function HighlightCard({
  highlight,
  onClick,
  onUpdateNote,
  onDelete,
  onChangeColor,
}: HighlightCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedNote, setEditedNote] = useState(highlight.note || "");
  const [showColorPicker, setShowColorPicker] = useState(false);

  const handleSaveNote = () => {
    onUpdateNote(editedNote);
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditedNote(highlight.note || "");
    setIsEditing(false);
  };

  const style = colorStyles[highlight.color];

  return (
    <div
      className={`p-3 border-l-4 ${style.border} hover:bg-gray-50 dark:hover:bg-[#242423] transition-colors cursor-pointer`}
      onClick={onClick}
    >
      {/* Highlighted text preview */}
      <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2 mb-2">
        "{highlight.selected_text}"
      </p>

      {/* Page indicator for PDFs */}
      {highlight.position.page !== undefined && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
          Page {highlight.position.page}
        </p>
      )}

      {/* Note section */}
      {isEditing ? (
        <div className="mt-2" onClick={(e) => e.stopPropagation()}>
          <textarea
            value={editedNote}
            onChange={(e) => setEditedNote(e.target.value)}
            placeholder="Add a note..."
            className="w-full p-2 text-sm rounded border border-gray-300 dark:border-[#333332] bg-white dark:bg-[#1c1c1b] text-gray-900 dark:text-white resize-none focus:outline-none focus:ring-2 focus:ring-amber-500"
            rows={3}
            autoFocus
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleSaveNote}
              className="flex items-center gap-1 px-2 py-1 text-xs bg-amber-600 text-white rounded hover:bg-amber-700 transition-colors"
            >
              <Check className="w-3 h-3" />
              Save
            </button>
            <button
              onClick={handleCancelEdit}
              className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-200 dark:bg-[#333332] text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-[#444443] transition-colors"
            >
              <X className="w-3 h-3" />
              Cancel
            </button>
          </div>
        </div>
      ) : highlight.note ? (
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 p-2 bg-gray-50 dark:bg-[#242423] rounded">
          {highlight.note}
        </p>
      ) : null}

      {/* Actions */}
      <div
        className="flex items-center justify-between mt-3 pt-2 border-t border-gray-100 dark:border-[#2a2a29]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Color picker */}
        <div className="relative">
          <button
            onClick={() => setShowColorPicker(!showColorPicker)}
            className={`w-5 h-5 rounded-full ${style.bg} hover:scale-110 transition-transform`}
            title="Change color"
          />
          {showColorPicker && (
            <div className="absolute bottom-full left-0 mb-1 flex gap-1 p-1.5 bg-white dark:bg-[#1c1c1b] rounded-lg shadow-lg border border-gray-200 dark:border-[#2a2a29]">
              {colors.map((color) => (
                <button
                  key={color}
                  onClick={() => {
                    onChangeColor(color);
                    setShowColorPicker(false);
                  }}
                  className={`w-5 h-5 rounded-full ${colorStyles[color].bg} hover:scale-110 transition-transform ${
                    highlight.color === color ? "ring-2 ring-offset-1 ring-gray-400" : ""
                  }`}
                />
              ))}
            </div>
          )}
        </div>

        {/* Edit and Delete buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => setIsEditing(true)}
            className="p-1 text-gray-500 hover:text-amber-600 dark:hover:text-amber-400 transition-colors"
            title={highlight.note ? "Edit note" : "Add note"}
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={onDelete}
            className="p-1 text-gray-500 hover:text-red-600 dark:hover:text-red-400 transition-colors"
            title="Delete highlight"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
