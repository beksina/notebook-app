"use client";

import React, { useRef, useCallback } from "react";
import { Highlight, TextSelection } from "@/types/highlight";

interface TextViewerProps {
  content: string;
  highlights: Highlight[];
  onTextSelect: (selection: TextSelection) => void;
}

export default function TextViewer({ content, highlights, onTextSelect }: TextViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Handle mouse up to capture text selection
  const handleMouseUp = useCallback(() => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !containerRef.current) return;

    const selectedText = selection.toString().trim();
    if (!selectedText) return;

    // Calculate offsets relative to the content
    const range = selection.getRangeAt(0);

    // Get all text before the selection start
    const preCaretRange = document.createRange();
    preCaretRange.selectNodeContents(containerRef.current);
    preCaretRange.setEnd(range.startContainer, range.startOffset);
    const startOffset = preCaretRange.toString().length;
    const endOffset = startOffset + selectedText.length;

    onTextSelect({
      text: selectedText,
      startOffset,
      endOffset,
    });
  }, [onTextSelect]);

  // Render content with highlights
  const renderHighlightedContent = () => {
    if (highlights.length === 0) {
      return content;
    }

    // Sort highlights by start offset
    const sorted = [...highlights]
      .filter((h) => h.position.start_offset !== undefined && h.position.end_offset !== undefined)
      .sort((a, b) => (a.position.start_offset ?? 0) - (b.position.start_offset ?? 0));

    if (sorted.length === 0) {
      return content;
    }

    // Build segments
    const segments: React.ReactElement[] = [];
    let lastEnd = 0;

    sorted.forEach((h, index) => {
      const start = h.position.start_offset ?? 0;
      const end = h.position.end_offset ?? start;

      // Add text before this highlight
      if (start > lastEnd) {
        segments.push(
          <span key={`text-${index}`}>{content.slice(lastEnd, start)}</span>
        );
      }

      // Add highlighted text
      segments.push(
        <mark
          key={`highlight-${h.id}`}
          className={`highlight-${h.color}`}
          data-highlight-id={h.id}
        >
          {content.slice(start, end)}
        </mark>
      );

      lastEnd = end;
    });

    // Add remaining text
    if (lastEnd < content.length) {
      segments.push(<span key="text-end">{content.slice(lastEnd)}</span>);
    }

    return segments;
  };

  return (
    <div
      ref={containerRef}
      className="h-full overflow-auto p-6 bg-white dark:bg-[#1c1c1b]"
      onMouseUp={handleMouseUp}
    >
      <pre className="whitespace-pre-wrap font-mono text-sm text-gray-800 dark:text-gray-200 leading-relaxed">
        {renderHighlightedContent()}
      </pre>
    </div>
  );
}
