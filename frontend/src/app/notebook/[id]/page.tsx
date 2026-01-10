"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Settings } from "lucide-react";
import SourceMaterialPanel from "@/components/SourceMaterialPanel";
import ChatInterface from "@/components/ChatInterface";
import { useEffect, useRef, useState } from "react";
import { useApi } from "@/hooks/useApi";

export default function NotebookPage() {
  const { api, isAuthenticated } = useApi();
  const params = useParams();
  const notebookId = params.id as string;
  const [notebook, setNotebook] = useState<Notebook | null>(null);

  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editedTitle, setEditedTitle] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const fetchNotebook = async () => {
      try {
        const notebook = await api.get(`/api/notebooks/${notebookId}`) as Notebook;
        setNotebook(notebook);
      } catch (e) {
        console.error(e);
      }
    }
    if (isAuthenticated) {
      fetchNotebook();
    }
  }, [isAuthenticated])

  useEffect(() => {
    if (isEditingTitle && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditingTitle]);

  const handleTitleClick = () => {
    setEditedTitle(notebook?.title || "");
    setIsEditingTitle(true);
  };

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEditedTitle(e.target.value);
  };

  const handleTitleBlur = async () => {
    setIsEditingTitle(false);

    // Only update if title actually changed and isn't empty
    if (editedTitle.trim() && editedTitle !== notebook?.title) {
      try {
        await api.patch(`/api/notebooks/${notebookId}`, { title: editedTitle.trim() });
        setNotebook(prev => prev ? { ...prev, title: editedTitle.trim() } : null);
      } catch (e) {
        console.error(e);
        // Revert to original title on error
        setEditedTitle(notebook?.title || "");
      }
    } else {
      // Revert if empty
      setEditedTitle(notebook?.title || "");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      inputRef.current?.blur();
    } else if (e.key === "Escape") {
      setEditedTitle(notebook?.title || "");
      setIsEditingTitle(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-[#141413]">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-white dark:bg-[#1c1c1b] border-b border-gray-200 dark:border-[#2a2a29]">
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-[#242423] transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </Link>
          {isEditingTitle ? (
            <input
              ref={inputRef}
              type="text"
              value={editedTitle}
              onChange={handleTitleChange}
              onBlur={handleTitleBlur}
              onKeyDown={handleKeyDown}
              className="text-xl font-semibold text-gray-900 dark:text-white bg-transparent border-b-2 border-amber-500 outline-none px-1 py-0.5"
            />
          ) : (
            <h1
              onClick={handleTitleClick}
              className="text-xl font-semibold text-gray-900 dark:text-white cursor-pointer hover:bg-gray-100 dark:hover:bg-[#242423] px-2 py-1 rounded transition-colors"
              title="Click to edit"
            >
              {notebook?.title}
            </h1>
          )}
        </div>

        <div className="flex items-center gap-4">
          <button
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-[#242423] transition-colors"
            aria-label="Settings"
          >
            <Settings className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>

          <button
            className="w-9 h-9 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-medium text-sm"
            aria-label="User profile"
          >
            U
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex gap-4 p-4 overflow-hidden">
        {/* Source Material Panel - 1/4 width */}
        <div className="w-1/4 min-w-[250px]">
          <SourceMaterialPanel notebookId={notebookId} />
        </div>

        {/* Chat Interface - 3/4 width */}
        <div className="flex-1">
          <ChatInterface notebookId={notebookId} />
        </div>
      </main>
    </div>
  );
}
