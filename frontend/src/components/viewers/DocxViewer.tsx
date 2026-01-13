"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import mammoth from "mammoth";
import { Loader2 } from "lucide-react";
import { Highlight, TextSelection } from "@/types/highlight";

interface DocxViewerProps {
  content: Blob;
  highlights: Highlight[];
  onTextSelect: (selection: TextSelection) => void;
}

export default function DocxViewer({ content, highlights, onTextSelect }: DocxViewerProps) {
  const [html, setHtml] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const convertDocx = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const arrayBuffer = await content.arrayBuffer();
        const result = await mammoth.convertToHtml({ arrayBuffer });

        setHtml(result.value);

        if (result.messages.length > 0) {
          console.warn("Mammoth conversion warnings:", result.messages);
        }
      } catch (err) {
        console.error("Failed to convert DOCX:", err);
        setError("Failed to load document");
      } finally {
        setIsLoading(false);
      }
    };

    convertDocx();
  }, [content]);

  // Handle text selection
  const handleMouseUp = useCallback(() => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !contentRef.current) return;

    const selectedText = selection.toString().trim();
    if (!selectedText) return;

    // Calculate offsets relative to the rendered content
    const range = selection.getRangeAt(0);

    const preCaretRange = document.createRange();
    preCaretRange.selectNodeContents(contentRef.current);
    preCaretRange.setEnd(range.startContainer, range.startOffset);
    const startOffset = preCaretRange.toString().length;
    const endOffset = startOffset + selectedText.length;

    onTextSelect({
      text: selectedText,
      startOffset,
      endOffset,
    });
  }, [onTextSelect]);

  // Apply highlights to the rendered DOM
  useEffect(() => {
    if (!contentRef.current || highlights.length === 0 || !html) return;

    // Small delay to ensure DOM is fully rendered
    const timeoutId = setTimeout(() => {
      if (!contentRef.current) return;

      // Remove existing highlight marks
      const existingMarks = contentRef.current.querySelectorAll("mark[data-highlight-id]");
      existingMarks.forEach((mark) => {
        const parent = mark.parentNode;
        if (parent) {
          while (mark.firstChild) {
            parent.insertBefore(mark.firstChild, mark);
          }
          parent.removeChild(mark);
        }
      });

      // Sort highlights by start offset
      const sortedHighlights = [...highlights]
        .filter((h) => h.position.start_offset !== undefined && h.position.end_offset !== undefined)
        .sort((a, b) => (a.position.start_offset ?? 0) - (b.position.start_offset ?? 0));

      if (sortedHighlights.length === 0) return;

      // Walk through text nodes and apply highlights
      const walker = document.createTreeWalker(
        contentRef.current,
        NodeFilter.SHOW_TEXT,
        null
      );

      let currentOffset = 0;
      const textNodes: { node: Text; start: number; end: number }[] = [];

      let node: Text | null;
      while ((node = walker.nextNode() as Text | null)) {
        const nodeLength = node.textContent?.length ?? 0;
        textNodes.push({
          node,
          start: currentOffset,
          end: currentOffset + nodeLength,
        });
        currentOffset += nodeLength;
      }

      // Apply highlights in reverse order
      for (let i = sortedHighlights.length - 1; i >= 0; i--) {
        const highlight = sortedHighlights[i];
        const highlightStart = highlight.position.start_offset ?? 0;
        const highlightEnd = highlight.position.end_offset ?? 0;

        for (let j = textNodes.length - 1; j >= 0; j--) {
          const { node: textNode, start: nodeStart, end: nodeEnd } = textNodes[j];

          if (nodeEnd <= highlightStart || nodeStart >= highlightEnd) continue;

          const localStart = Math.max(0, highlightStart - nodeStart);
          const localEnd = Math.min(textNode.textContent?.length ?? 0, highlightEnd - nodeStart);

          if (localStart >= localEnd) continue;

          try {
            const range = document.createRange();
            range.setStart(textNode, localStart);
            range.setEnd(textNode, localEnd);

            const mark = document.createElement("mark");
            mark.className = `highlight-${highlight.color}`;
            mark.setAttribute("data-highlight-id", highlight.id);
            range.surroundContents(mark);
          } catch {
            continue;
          }
        }
      }
    }, 50);

    return () => clearTimeout(timeoutId);
  }, [highlights, html]);

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-white dark:bg-[#1c1c1b]">
        <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-white dark:bg-[#1c1c1b] text-red-500">
        {error}
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto p-6 bg-white dark:bg-[#1c1c1b]" onMouseUp={handleMouseUp}>
      <div
        ref={contentRef}
        className="max-w-4xl mx-auto prose prose-gray dark:prose-invert prose-headings:text-gray-900 dark:prose-headings:text-white prose-p:text-gray-700 dark:prose-p:text-gray-300 prose-a:text-amber-600 dark:prose-a:text-amber-400"
        dangerouslySetInnerHTML={{ __html: html || "" }}
      />
    </div>
  );
}
