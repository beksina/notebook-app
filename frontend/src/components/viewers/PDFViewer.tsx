"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Loader2 } from "lucide-react";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { Highlight, TextSelection } from "@/types/highlight";

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PDFViewerProps {
  content: Blob;
  highlights: Highlight[];
  onTextSelect: (selection: TextSelection) => void;
}

// Map highlight colors to rgba values
const highlightColors: Record<string, string> = {
  yellow: "rgba(253, 224, 71, 0.4)",
  green: "rgba(134, 239, 172, 0.4)",
  blue: "rgba(147, 197, 253, 0.4)",
  pink: "rgba(249, 168, 212, 0.4)",
};

export default function PDFViewer({ content, highlights, onTextSelect }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [highlightRects, setHighlightRects] = useState<
    Array<{ id: string; rects: DOMRect[]; color: string }>
  >([]);
  const pageRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Create object URL from blob
  useEffect(() => {
    const url = URL.createObjectURL(content);
    setPdfUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [content]);

  // Handle text selection
  const handleMouseUp = useCallback(() => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) return;

    const selectedText = selection.toString().trim();
    if (!selectedText) return;

    const range = selection.getRangeAt(0);
    const textLayer = pageRef.current?.querySelector(".react-pdf__Page__textContent");
    if (!textLayer || !textLayer.contains(range.commonAncestorContainer)) return;

    const preCaretRange = document.createRange();
    preCaretRange.selectNodeContents(textLayer);
    preCaretRange.setEnd(range.startContainer, range.startOffset);
    const startOffset = preCaretRange.toString().length;
    const endOffset = startOffset + selectedText.length;

    onTextSelect({
      text: selectedText,
      startOffset,
      endOffset,
      page: pageNumber,
    });
  }, [onTextSelect, pageNumber]);

  // Calculate highlight rectangles using Range API
  const calculateHighlightRects = useCallback(() => {
    if (!pageRef.current) return;

    const textLayer = pageRef.current.querySelector(".react-pdf__Page__textContent");
    if (!textLayer) return;

    const pageHighlights = highlights.filter(
      (h) =>
        h.position.page === pageNumber &&
        h.position.start_offset !== undefined &&
        h.position.end_offset !== undefined
    );

    if (pageHighlights.length === 0) {
      setHighlightRects([]);
      return;
    }

    // Build a map of character offsets to text nodes
    const walker = document.createTreeWalker(textLayer, NodeFilter.SHOW_TEXT, null);
    const textNodes: { node: Text; start: number; end: number }[] = [];
    let currentOffset = 0;

    let node: Text | null;
    while ((node = walker.nextNode() as Text | null)) {
      const len = node.textContent?.length ?? 0;
      textNodes.push({ node, start: currentOffset, end: currentOffset + len });
      currentOffset += len;
    }

    const newHighlightRects: Array<{ id: string; rects: DOMRect[]; color: string }> = [];
    const containerRect = pageRef.current.getBoundingClientRect();

    for (const highlight of pageHighlights) {
      const hStart = highlight.position.start_offset ?? 0;
      const hEnd = highlight.position.end_offset ?? 0;

      // Find start and end nodes
      let startNode: Text | null = null;
      let startLocalOffset = 0;
      let endNode: Text | null = null;
      let endLocalOffset = 0;

      for (const { node: textNode, start, end } of textNodes) {
        if (startNode === null && hStart >= start && hStart < end) {
          startNode = textNode;
          startLocalOffset = hStart - start;
        }
        if (hEnd > start && hEnd <= end) {
          endNode = textNode;
          endLocalOffset = hEnd - start;
        }
      }

      if (!startNode || !endNode) continue;

      try {
        const range = document.createRange();
        range.setStart(startNode, startLocalOffset);
        range.setEnd(endNode, endLocalOffset);

        // Get all client rects (handles multi-line selections)
        const rects = Array.from(range.getClientRects()).map((rect) => {
          return new DOMRect(
            rect.left - containerRect.left,
            rect.top - containerRect.top,
            rect.width,
            rect.height
          );
        });

        if (rects.length > 0) {
          newHighlightRects.push({
            id: highlight.id,
            rects,
            color: highlight.color,
          });
        }
      } catch {
        continue;
      }
    }

    setHighlightRects(newHighlightRects);
  }, [highlights, pageNumber]);

  // Recalculate highlights when page loads or scale changes
  useEffect(() => {
    // Small delay to ensure text layer is rendered
    const timer = setTimeout(calculateHighlightRects, 100);
    return () => clearTimeout(timer);
  }, [calculateHighlightRects, scale, pageNumber]);

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setPageNumber(1);
  }, []);

  const goToPrevPage = () => setPageNumber((prev) => Math.max(prev - 1, 1));
  const goToNextPage = () => setPageNumber((prev) => Math.min(prev + 1, numPages || 1));
  const zoomIn = () => setScale((prev) => Math.min(prev + 0.25, 1.5));
  const zoomOut = () => setScale((prev) => Math.max(prev - 0.25, 0.5));

  if (!pdfUrl) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-100 dark:bg-[#141413]">
      {/* Controls */}
      <div className="flex items-center justify-between px-4 py-2 bg-white dark:bg-[#1c1c1b] border-b border-gray-200 dark:border-[#2a2a29]">
        <div className="flex items-center gap-2">
          <button
            onClick={goToPrevPage}
            disabled={pageNumber <= 1}
            className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-[#242423] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400 min-w-[100px] text-center">
            Page {pageNumber} of {numPages || "..."}
          </span>
          <button
            onClick={goToNextPage}
            disabled={pageNumber >= (numPages || 1)}
            className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-[#242423] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronRight className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={zoomOut}
            disabled={scale <= 0.5}
            className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-[#242423] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ZoomOut className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400 min-w-[60px] text-center">
            {Math.round(scale * 100)}%
          </span>
          <button
            onClick={zoomIn}
            disabled={scale >= 1.5}
            className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-[#242423] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ZoomIn className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
        </div>
      </div>

      {/* PDF Document */}
      <div className="flex-1 overflow-auto flex justify-center p-4" onMouseUp={handleMouseUp}>
        <Document
          file={pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
            </div>
          }
          error={
            <div className="flex items-center justify-center h-full text-red-500">
              Failed to load PDF
            </div>
          }
        >
          <div ref={pageRef} style={{ position: "relative" }}>
            <Page
              pageNumber={pageNumber}
              scale={scale}
              className="shadow-lg"
              renderTextLayer={true}
              renderAnnotationLayer={true}
              onRenderSuccess={calculateHighlightRects}
            />
            {/* Highlight overlay layer */}
            <div
              ref={containerRef}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                pointerEvents: "none",
                zIndex: 1,
              }}
            >
              {highlightRects.map(({ id, rects, color }) =>
                rects.map((rect, i) => (
                  <div
                    key={`${id}-${i}`}
                    style={{
                      position: "absolute",
                      left: rect.x,
                      top: rect.y,
                      width: rect.width,
                      height: rect.height,
                      backgroundColor: highlightColors[color] || highlightColors.yellow,
                      borderRadius: 2,
                      mixBlendMode: "multiply",
                    }}
                  />
                ))
              )}
            </div>
          </div>
        </Document>
      </div>
    </div>
  );
}