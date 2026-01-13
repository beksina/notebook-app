"use client";

import { useRef, useCallback, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Highlight, TextSelection } from "@/types/highlight";

interface MarkdownViewerProps {
  content: string;
  highlights: Highlight[];
  onTextSelect: (selection: TextSelection) => void;
}

export default function MarkdownViewer({ content, highlights, onTextSelect }: MarkdownViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const [renderKey, setRenderKey] = useState(0);

  // Handle mouse up to capture text selection
  const handleMouseUp = useCallback(() => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !contentRef.current) return;

    const selectedText = selection.toString().trim();
    if (!selectedText) return;

    // Calculate offsets relative to the rendered content
    const range = selection.getRangeAt(0);

    // Get all text before the selection start
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
    if (!contentRef.current || highlights.length === 0) return;

    // Remove existing highlight marks (clean slate)
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

    // First pass: collect all text nodes with their offsets
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

    // Apply highlights in reverse order to avoid offset issues
    for (let i = sortedHighlights.length - 1; i >= 0; i--) {
      const highlight = sortedHighlights[i];
      const highlightStart = highlight.position.start_offset ?? 0;
      const highlightEnd = highlight.position.end_offset ?? 0;

      // Find text nodes that overlap with this highlight
      for (let j = textNodes.length - 1; j >= 0; j--) {
        const { node: textNode, start: nodeStart, end: nodeEnd } = textNodes[j];

        // Check if this text node overlaps with the highlight
        if (nodeEnd <= highlightStart || nodeStart >= highlightEnd) continue;

        // Calculate the portion of this text node to highlight
        const localStart = Math.max(0, highlightStart - nodeStart);
        const localEnd = Math.min(textNode.textContent?.length ?? 0, highlightEnd - nodeStart);

        if (localStart >= localEnd) continue;

        // Split the text node and wrap the highlighted portion
        try {
          const range = document.createRange();
          range.setStart(textNode, localStart);
          range.setEnd(textNode, localEnd);

          const mark = document.createElement("mark");
          mark.className = `highlight-${highlight.color}`;
          mark.setAttribute("data-highlight-id", highlight.id);
          range.surroundContents(mark);
        } catch {
          // Range may cross element boundaries, skip this node
          continue;
        }
      }
    }
  }, [highlights, renderKey]);

  // Trigger re-render when content changes to reapply highlights
  useEffect(() => {
    setRenderKey((k) => k + 1);
  }, [content]);

  return (
    <div
      ref={containerRef}
      className="h-full overflow-auto p-6 bg-white dark:bg-[#1c1c1b]"
      onMouseUp={handleMouseUp}
    >
      <div ref={contentRef} className="max-w-4xl mx-auto">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ children }) => (
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mt-8 mb-4 first:mt-0">
                {children}
              </h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-6 mb-3">
                {children}
              </h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mt-5 mb-2">
                {children}
              </h3>
            ),
            h4: ({ children }) => (
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mt-4 mb-2">
                {children}
              </h4>
            ),
            p: ({ children }) => (
              <p className="text-gray-700 dark:text-gray-300 my-3 leading-7">
                {children}
              </p>
            ),
            ul: ({ children }) => (
              <ul className="list-disc list-outside ml-6 my-3 space-y-1 text-gray-700 dark:text-gray-300">
                {children}
              </ul>
            ),
            ol: ({ children }) => (
              <ol className="list-decimal list-outside ml-6 my-3 space-y-1 text-gray-700 dark:text-gray-300">
                {children}
              </ol>
            ),
            li: ({ children }) => <li className="leading-7">{children}</li>,
            blockquote: ({ children }) => (
              <blockquote className="border-l-4 border-amber-500 pl-4 my-4 italic text-gray-600 dark:text-gray-400">
                {children}
              </blockquote>
            ),
            code: ({ children, className }) => {
              const isCodeBlock = className?.includes("language-");
              return isCodeBlock ? (
                <code className={className}>{children}</code>
              ) : (
                <code className="bg-gray-100 dark:bg-[#242423] px-1.5 py-0.5 rounded text-sm text-amber-600 dark:text-amber-400">
                  {children}
                </code>
              );
            },
            pre: ({ children }) => (
              <pre className="bg-gray-100 dark:bg-[#242423] p-4 rounded-lg overflow-x-auto my-4 text-sm">
                {children}
              </pre>
            ),
            a: ({ href, children }) => (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-amber-600 dark:text-amber-400 hover:underline"
              >
                {children}
              </a>
            ),
            table: ({ children }) => (
              <div className="overflow-x-auto my-4">
                <table className="min-w-full border-collapse border border-gray-200 dark:border-gray-700">
                  {children}
                </table>
              </div>
            ),
            th: ({ children }) => (
              <th className="border border-gray-200 dark:border-gray-700 px-4 py-2 bg-gray-50 dark:bg-[#242423] text-left font-semibold text-gray-900 dark:text-white">
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td className="border border-gray-200 dark:border-gray-700 px-4 py-2 text-gray-700 dark:text-gray-300">
                {children}
              </td>
            ),
            hr: () => <hr className="my-6 border-gray-200 dark:border-gray-700" />,
            img: ({ src, alt }) => (
              <img
                src={src}
                alt={alt || ""}
                className="max-w-full h-auto rounded-lg my-4"
              />
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
