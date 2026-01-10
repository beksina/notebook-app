"use client";

import { useEffect, useState } from "react";
import { Upload, FileText, X, Plus, Search, Loader2, Info } from "lucide-react";
import { useApi } from "@/hooks/useApi";

interface SourceFile {
  id: string;
  name: string;
  type: string;
  title?: string;
  processed?: boolean;
}

export default function SourceMaterialPanel({ notebookId } : { notebookId: string }) {
  const { api, isAuthenticated } = useApi();
  const [files, setFiles] = useState<SourceFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchMaterials = async() => {
      try {
        const materials = await api.get<any[]>(`/api/notebooks/${notebookId}/materials`);
        setFiles(materials.map(m => ({ id: m.id, name: m.title, type: m.type, processed: m.processed })));
      } catch(e) {
        console.error(e);
      }
    }
    if (isAuthenticated) {
      setIsLoading(true);
      fetchMaterials();
      setIsLoading(false);
    }
  }, [isAuthenticated, notebookId, api])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    await addFiles(droppedFiles);
  };

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      addFiles(selectedFiles);
    }
  };

  const addFiles = async (newFiles: File[]) => {
    for (const file of newFiles) {
      try {
        const uploaded = await api.uploadFile<SourceFile>(
          `/api/notebooks/${notebookId}/materials/upload`,
          file
        );
        setFiles((prev) => [...prev, { id: uploaded.id, name: uploaded.title || file.name, type: file.type }]);
      } catch (error) {
        console.error(`Failed to upload ${file.name}:`, error);
      }
    }
  };

  const removeFile = async (id: string) => {
    try {
      await api.delete(`/api/notebooks/${notebookId}/materials/${id}`);
      setFiles((prev) => prev.filter((f) => f.id !== id));
    } catch(e) {
      console.error(e)
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setTimeout(() => {
      setIsSearching(false);
    }, 2000);
  };

  if (isLoading) {
    // TODO: add loading thingy
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-[#1c1c1b] rounded-xl border border-gray-200 dark:border-[#2a2a29]">
      <div className="p-4 border-b border-gray-200 dark:border-[#2a2a29]">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="font-semibold text-gray-900 dark:text-white">Source Materials</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Upload materials to study from
            </p>
          </div>
          <div className="relative group">
            <Info className="w-4 h-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 cursor-help" />
            <div className="absolute right-0 top-6 w-48 p-2 bg-gray-900 dark:bg-gray-800 text-white text-xs rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
              <p className="font-medium mb-1">Supported file types:</p>
              <ul className="space-y-0.5 text-gray-300">
                <li>• PDF (.pdf)</li>
                <li>• Word (.doc, .docx)</li>
                <li>• Text (.txt)</li>
                <li>• Markdown (.md)</li>
              </ul>
              <div className="absolute -top-1 right-2 w-2 h-2 bg-gray-900 dark:bg-gray-800 rotate-45"></div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Upload Section - Compact */}
        {files.length === 0 && <label
          className={`flex items-center justify-center gap-3 h-60 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
            isDragging
              ? "border-amber-500 bg-amber-50 dark:bg-amber-900/20"
              : "border-gray-300 dark:border-[#333332] hover:border-amber-400 dark:hover:border-amber-600"
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <Upload className="w-5 h-5 text-gray-400 dark:text-gray-500" />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Drop files or click to upload
          </span>
          <input
            type="file"
            multiple
            className="hidden"
            onChange={handleFileInput}
            accept=".pdf,.doc,.docx,.txt,.md"
          />
        </label>}

        {/* Search Section */}
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
            Search for materials online
          </p>
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search topic..."
                className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-[#333332] bg-gray-50 dark:bg-[#242423] text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              />
            </div>
            <button
              type="submit"
              disabled={!searchQuery.trim() || isSearching}
              className="px-3 py-2 bg-amber-600 hover:bg-amber-700 disabled:bg-amber-600/50 disabled:cursor-not-allowed text-white text-sm rounded-lg transition-colors"
            >
              {isSearching ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                "Search"
              )}
            </button>
          </form>
        </div>

        {/* Files List */}
        {files.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
              Uploaded Files
            </p>
            {files.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-2 p-2 rounded-lg bg-gray-50 dark:bg-[#242423] group"
              >
                <FileText className="w-4 h-4 text-amber-500 flex-shrink-0" />
                <span className="text-sm text-gray-700 dark:text-gray-300 truncate flex-1">
                  {file.name}
                </span>
                <button
                  onClick={() => removeFile(file.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-200 dark:hover:bg-[#333332] rounded transition-all"
                >
                  <X className="w-3 h-3 text-gray-500" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {files.length > 0 && (
        <div className="p-4 border-t border-gray-200 dark:border-[#2a2a29]">
          <label className="flex items-center justify-center gap-2 w-full py-2 px-3 text-sm font-medium text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 hover:bg-amber-100 dark:hover:bg-amber-900/30 rounded-lg cursor-pointer transition-colors">
            <Plus className="w-4 h-4" />
            Add more files
            <input
              type="file"
              multiple
              className="hidden"
              onChange={handleFileInput}
              accept=".pdf,.doc,.docx,.txt,.md"
            />
          </label>
        </div>
      )}
    </div>
  );
}