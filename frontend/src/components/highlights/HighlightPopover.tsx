"use client";

import { useEffect, useRef } from "react";
import { HighlightColor } from "@/types/highlight";

interface HighlightPopoverProps {
  position: { x: number; y: number };
  onSelectColor: (color: HighlightColor) => void;
  onClose: () => void;
}

const colors: { color: HighlightColor; bg: string; hover: string }[] = [
  { color: "yellow", bg: "bg-yellow-300", hover: "hover:bg-yellow-400" },
  { color: "green", bg: "bg-green-300", hover: "hover:bg-green-400" },
  { color: "blue", bg: "bg-blue-300", hover: "hover:bg-blue-400" },
  { color: "pink", bg: "bg-pink-300", hover: "hover:bg-pink-400" },
];

export default function HighlightPopover({
  position,
  onSelectColor,
  onClose,
}: HighlightPopoverProps) {
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [onClose]);

  return (
    <div
      ref={popoverRef}
      className="fixed z-50 flex gap-1.5 p-2 bg-white dark:bg-[#1c1c1b] rounded-lg shadow-lg border border-gray-200 dark:border-[#2a2a29]"
      style={{
        left: Math.min(position.x, window.innerWidth - 150),
        top: position.y,
      }}
    >
      {colors.map(({ color, bg, hover }) => (
        <button
          key={color}
          onClick={() => onSelectColor(color)}
          className={`w-7 h-7 rounded-full ${bg} ${hover} transition-transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500`}
          aria-label={`Highlight ${color}`}
          title={color.charAt(0).toUpperCase() + color.slice(1)}
        />
      ))}
    </div>
  );
}
