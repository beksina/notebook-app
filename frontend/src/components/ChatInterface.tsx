"use client";

import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { useApi } from "@/hooks/useApi";
import { SSEEvent } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface Source {
  title: string;
  similarity: number;
  preview: string;
}

interface ChatInterfaceProps {
  notebookId: string;
}

export default function ChatInterface({ notebookId }: ChatInterfaceProps) {
  const { api, isAuthenticated } = useApi();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<string>("");
  const [sources, setSources] = useState<Source[]>([]);
  const [streamingContent, setStreamingContent] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<(() => void) | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortRef.current) {
        abortRef.current();
      }
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !isAuthenticated) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setStreamingContent("");
    setSources([]);
    setStatus("");

    // Prepare chat history for API
    const history = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    // Track accumulated content in a local variable for the closure
    let accumulatedContent = "";

    // Start streaming
    abortRef.current = api.streamPost(
      `/api/notebooks/${notebookId}/chat`,
      {
        message: userMessage.content,
        history,
        n_results: 5,
      },
      (event: SSEEvent) => {
        switch (event.event.trim()) {
          case "status":
            setStatus(event.data.message as string);
            break;

          case "sources":
            setSources(event.data.sources as Source[]);
            break;

          case "content":
            accumulatedContent += event.data.text as string;
            setStreamingContent(accumulatedContent);
            break;

          case "done":
            // Finalize the assistant message
            setMessages((prev) => [
              ...prev,
              {
                id: crypto.randomUUID(),
                role: "assistant",
                content: accumulatedContent,
              },
            ]);
            setStreamingContent("");
            setStatus("");
            setIsLoading(false);
            break;

          case "error":
            setStatus(`Error: ${event.data.message}`);
            setIsLoading(false);
            break;
        }
      }
    );
  };

  return (
    <div className="h-full flex flex-col bg-white dark:bg-[#1c1c1b] rounded-xl border border-gray-200 dark:border-[#2a2a29]">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                message.role === "user"
                  ? "bg-amber-600 text-white"
                  : "bg-gray-100 dark:bg-[#242423] text-gray-900 dark:text-white"
              }`}
            >
              <div className="text-sm [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => <h1 className="text-xl font-bold my-2">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-lg font-bold my-2">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-base font-semibold my-2">{children}</h3>,
                    p: ({ children }) => <p className="my-2">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>,
                    li: ({ children }) => <li>{children}</li>,
                    strong: ({ children }) => <strong className="font-bold">{children}</strong>,
                    em: ({ children }) => <em className="italic">{children}</em>,
                    pre: ({ children }) => (
                      <pre className="bg-gray-200 dark:bg-[#1c1c1b] p-3 rounded-lg overflow-x-auto my-2 text-xs">
                        {children}
                      </pre>
                    ),
                    code: ({ children, className }) => {
                      const isCodeBlock = className?.includes("language-");
                      return isCodeBlock ? (
                        <code className={className}>{children}</code>
                      ) : (
                        <code className="bg-gray-200 dark:bg-[#1c1c1b] px-1.5 py-0.5 rounded text-xs">{children}</code>
                      );
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        ))}

        {/* Streaming response */}
        {isLoading && (
          <div className="flex flex-col gap-2">
            {/* Status indicator */}
            {status && (
              <div className="text-sm text-gray-500 dark:text-gray-400 italic">
                {status}
              </div>
            )}

            {/* Sources preview */}
            {sources.length > 0 && (
              <div className="text-xs text-gray-400 dark:text-gray-500">
                Found {sources.length} relevant source{sources.length !== 1 ? "s" : ""}
              </div>
            )}

            {/* Streaming content */}
            {streamingContent && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-2xl px-4 py-2 bg-gray-100 dark:bg-[#242423] text-gray-900 dark:text-white">
                  <div className="text-sm [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({ children }) => <h1 className="text-xl font-bold my-2">{children}</h1>,
                        h2: ({ children }) => <h2 className="text-lg font-bold my-2">{children}</h2>,
                        h3: ({ children }) => <h3 className="text-base font-semibold my-2">{children}</h3>,
                        p: ({ children }) => <p className="my-2">{children}</p>,
                        ul: ({ children }) => <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>,
                        li: ({ children }) => <li>{children}</li>,
                        strong: ({ children }) => <strong className="font-bold">{children}</strong>,
                        em: ({ children }) => <em className="italic">{children}</em>,
                        pre: ({ children }) => (
                          <pre className="bg-gray-200 dark:bg-[#1c1c1b] p-3 rounded-lg overflow-x-auto my-2 text-xs">
                            {children}
                          </pre>
                        ),
                        code: ({ children, className }) => {
                          const isCodeBlock = className?.includes("language-");
                          return isCodeBlock ? (
                            <code className={className}>{children}</code>
                          ) : (
                            <code className="bg-gray-200 dark:bg-[#1c1c1b] px-1.5 py-0.5 rounded text-xs">{children}</code>
                          );
                        },
                      }}
                    >
                      {streamingContent}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            )}

            {/* Loading dots (only when no content yet) */}
            {!streamingContent && !status.startsWith("Error") && (
              <div className="flex justify-start">
                <div className="bg-gray-100 dark:bg-[#242423] rounded-2xl px-4 py-2">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.1s]" />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <form
        onSubmit={handleSubmit}
        className="p-4 border-t border-gray-200 dark:border-[#2a2a29]"
      >
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your materials..."
            className="flex-1 px-4 py-2 rounded-xl border border-gray-300 dark:border-[#333332] bg-gray-50 dark:bg-[#242423] text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-700 disabled:bg-amber-600/50 disabled:cursor-not-allowed text-white rounded-xl transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
}
