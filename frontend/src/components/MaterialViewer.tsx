"use client";

import { useEffect, useState } from "react";
import { Loader2, AlertCircle, PanelRightClose, PanelRight } from "lucide-react";
import { useApi } from "@/hooks/useApi";
import { useHighlights } from "@/hooks/useHighlights";
import { Highlight, HighlightColor, TextSelection } from "@/types/highlight";
import TextViewer from "./viewers/TextViewer";
import MarkdownViewer from "./viewers/MarkdownViewer";
import PDFViewer from "./viewers/PDFViewer";
import DocxViewer from "./viewers/DocxViewer";
import HighlightPopover from "./highlights/HighlightPopover";
import NotesSidebar from "./highlights/NotesSidebar";

interface MaterialViewerProps {
  notebookId: string;
  material: {
    id: string;
    title: string;
    type: string;
  };
  onClose: () => void;
}

type FileType = "pdf" | "txt" | "md" | "docx" | "unknown";

function getFileType(title: string, type: string): FileType {
  const extension = title.split(".").pop()?.toLowerCase();

  if (extension === "pdf" || type === "pdf") return "pdf";
  if (extension === "txt") return "txt";
  if (extension === "md" || extension === "markdown") return "md";
  if (extension === "docx" || extension === "doc") return "docx";

  // Fallback based on MIME type
  if (type.includes("pdf")) return "pdf";
  if (type.includes("text/plain")) return "txt";
  if (type.includes("markdown")) return "md";
  if (type.includes("word") || type.includes("document")) return "docx";

  return "unknown";
}

export default function MaterialViewer({ notebookId, material, onClose }: MaterialViewerProps) {
  const { api } = useApi();
  const [content, setContent] = useState<Blob | string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);

  // Selection popover state
  const [selectionPopover, setSelectionPopover] = useState<{
    position: { x: number; y: number };
    selection: TextSelection;
  } | null>(null);

  // Highlights state
  const {
    highlights,
    isLoading: highlightsLoading,
    createHighlight,
    updateHighlight,
    deleteHighlight,
  } = useHighlights(notebookId, material.id);

  const fileType = getFileType(material.title, material.type);

  useEffect(() => {
    const fetchContent = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const blob = await api.fetchBlob(
          `/api/notebooks/${notebookId}/materials/${material.id}/content`
        );

        // For text-based formats, convert to string
        if (fileType === "txt" || fileType === "md") {
          const text = await blob.text();
          setContent(text);
        } else {
          // For PDF and DOCX, keep as blob
          setContent(blob);
        }
      } catch (err) {
        console.error("Failed to fetch material content:", err);
        setError(err instanceof Error ? err.message : "Failed to load content");
      } finally {
        setIsLoading(false);
      }
    };

    fetchContent();
  }, [api, notebookId, material.id, fileType]);

  // Handle text selection from viewers
  const handleTextSelect = (selection: TextSelection) => {
    if (!selection.text.trim()) return;

    const domSelection = window.getSelection();
    if (!domSelection || domSelection.rangeCount === 0) return;

    const range = domSelection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    setSelectionPopover({
      position: { x: rect.left + rect.width / 2 - 70, y: rect.bottom + 8 },
      selection,
    });
  };

  // Handle color selection from popover
  const handleSelectColor = async (color: HighlightColor) => {
    if (!selectionPopover) return;

    try {
      await createHighlight({
        position: {
          start_offset: selectionPopover.selection.startOffset,
          end_offset: selectionPopover.selection.endOffset,
          page: selectionPopover.selection.page,
        },
        selected_text: selectionPopover.selection.text,
        color,
      });
    } catch (err) {
      console.error("Failed to create highlight:", err);
    }

    setSelectionPopover(null);
    window.getSelection()?.removeAllRanges();
  };

  // Handle clicking a highlight in the sidebar (scroll to it)
  const handleHighlightClick = (highlight: Highlight) => {
    // For now, just log. In the future, scroll to the highlight
    console.log("Navigate to highlight:", highlight);
  };

  // Handle note update
  const handleUpdateNote = async (id: string, note: string) => {
    try {
      await updateHighlight(id, { note: note || undefined });
    } catch (err) {
      console.error("Failed to update note:", err);
    }
  };

  // Handle highlight deletion
  const handleDeleteHighlight = async (id: string) => {
    try {
      await deleteHighlight(id);
    } catch (err) {
      console.error("Failed to delete highlight:", err);
    }
  };

  // Handle color change
  const handleChangeColor = async (id: string, color: HighlightColor) => {
    try {
      await updateHighlight(id, { color });
    } catch (err) {
      console.error("Failed to change color:", err);
    }
  };

  if (isLoading) {
    return (
      <div className="h-full flex flex-col items-center justify-center bg-white dark:bg-[#1c1c1b] rounded-xl border border-gray-200 dark:border-[#2a2a29]">
        <Loader2 className="w-8 h-8 animate-spin text-amber-500 mb-4" />
        <p className="text-gray-500 dark:text-gray-400">Loading {material.title}...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center bg-white dark:bg-[#1c1c1b] rounded-xl border border-gray-200 dark:border-[#2a2a29]">
        <AlertCircle className="w-8 h-8 text-red-500 mb-4" />
        <p className="text-red-500 mb-2">Failed to load material</p>
        <p className="text-gray-500 dark:text-gray-400 text-sm">{error}</p>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="h-full flex flex-col items-center justify-center bg-white dark:bg-[#1c1c1b] rounded-xl border border-gray-200 dark:border-[#2a2a29]">
        <AlertCircle className="w-8 h-8 text-gray-400 mb-4" />
        <p className="text-gray-500 dark:text-gray-400">No content available</p>
      </div>
    );
  }

  return (
    <div className="h-full flex bg-white dark:bg-[#1c1c1b] rounded-xl border border-gray-200 dark:border-[#2a2a29] overflow-hidden">
      {/* Main viewer area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Toolbar */}
        <div className="flex items-center justify-end px-3 py-2 border-b border-gray-200 dark:border-[#2a2a29]">
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-[#242423] transition-colors"
            title={showSidebar ? "Hide notes" : "Show notes"}
          >
            {showSidebar ? (
              <PanelRightClose className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            ) : (
              <PanelRight className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            )}
          </button>
        </div>

        {/* Viewer content */}
        <div className="flex-1 min-h-0 overflow-hidden">
          {fileType === "txt" && typeof content === "string" && (
            <TextViewer
              content={content}
              highlights={highlights}
              onTextSelect={handleTextSelect}
            />
          )}
          {fileType === "md" && typeof content === "string" && (
            <MarkdownViewer
              content={content}
              highlights={highlights}
              onTextSelect={handleTextSelect}
            />
          )}
          {fileType === "pdf" && content instanceof Blob && (
            <PDFViewer
              content={content}
              highlights={highlights}
              onTextSelect={handleTextSelect}
            />
          )}
          {fileType === "docx" && content instanceof Blob && (
            <DocxViewer
              content={content}
              highlights={highlights}
              onTextSelect={handleTextSelect}
            />
          )}
          {fileType === "unknown" && (
            <div className="h-full flex flex-col items-center justify-center">
              <AlertCircle className="w-8 h-8 text-amber-500 mb-4" />
              <p className="text-gray-500 dark:text-gray-400">
                Unsupported file type
              </p>
              <p className="text-gray-400 dark:text-gray-500 text-sm mt-1">
                Cannot preview this file format
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Notes Sidebar */}
      {showSidebar && (
        <NotesSidebar
          highlights={highlights}
          onHighlightClick={handleHighlightClick}
          onUpdateNote={handleUpdateNote}
          onDeleteHighlight={handleDeleteHighlight}
          onChangeColor={handleChangeColor}
        />
      )}

      {/* Highlight Popover */}
      {selectionPopover && (
        <HighlightPopover
          position={selectionPopover.position}
          onSelectColor={handleSelectColor}
          onClose={() => {
            setSelectionPopover(null);
            window.getSelection()?.removeAllRanges();
          }}
        />
      )}
    </div>
  );
}
