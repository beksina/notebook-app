const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FetchOptions extends RequestInit {
  token?: string;
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  async fetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
    const { token, ...fetchOptions } = options;

    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(fetchOptions.headers || {}),
    };

    // Add JWT token to Authorization header if available
    const effectiveToken = token || this.token;
    if (effectiveToken) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${effectiveToken}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...fetchOptions,
      headers,
      credentials: 'include'
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  // Convenience methods
  get<T>(endpoint: string, options?: FetchOptions) {
    return this.fetch<T>(endpoint, { ...options, method: "GET" });
  }

  post<T>(endpoint: string, data?: unknown, options?: FetchOptions) {
    return this.fetch<T>(endpoint, {
      ...options,
      method: "POST",
      body: data ? JSON.stringify(data) : undefined
    });
  }

  patch<T>(endpoint: string, data?: unknown, options?: FetchOptions) {
    return this.fetch<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  delete<T>(endpoint: string, options?: FetchOptions) {
    return this.fetch<T>(endpoint, { ...options, method: "DELETE" });
  }

  async fetchBlob(endpoint: string): Promise<Blob> {
    const headers: HeadersInit = {};
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      headers,
      credentials: "include",
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.blob();
  }

  async fetchText(endpoint: string): Promise<string> {
    const blob = await this.fetchBlob(endpoint);
    return blob.text();
  }

  async uploadFile<T>(endpoint: string, file: File, title?: string): Promise<T> {
    const formData = new FormData();
    formData.append("file", file);
    if (title) {
      formData.append("title", title);
    }

    const headers: HeadersInit = {};
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      method: "POST",
      headers,
      body: formData,
      credentials: "include",
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  /**
   * Stream SSE events from a POST endpoint.
   * @param endpoint API endpoint
   * @param data Request body
   * @param onEvent Callback for each SSE event
   * @returns Cleanup function to abort the stream
   */
  streamPost(
    endpoint: string,
    data: unknown,
    onEvent: (event: SSEEvent) => void
  ): () => void {
    const abortController = new AbortController();

    const fetchStream = async () => {
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };
      if (this.token) {
        headers["Authorization"] = `Bearer ${this.token}`;
      }

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers,
        body: JSON.stringify(data),
        signal: abortController.signal,
        credentials: "include",
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Request failed" }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("No response body");
      }

      let buffer = "";
      let currentEvent = "";
      let currentData = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7);
          } else if (line.startsWith("data: ")) {
            currentData = line.slice(6);
          } else {
            // Empty line = end of event
            if (currentEvent && currentData) {
              try {
                onEvent({
                  event: currentEvent as SSEEventType,
                  data: JSON.parse(currentData),
                });
              } catch (e) {
                console.error("Failed to parse SSE event:", e);
              }
            }
            // Reset for next event
            currentEvent = "";
            currentData = "";
          }
        }
      }
    };

    fetchStream().catch((e) => {
      if (e.name !== "AbortError") {
        console.error("Stream error:", e);
        onEvent({
          event: "error",
          data: { message: e.message },
        });
      }
    });

    return () => abortController.abort();
  }
}

// SSE Types
export type SSEEventType = "status" | "content" | "sources" | "error" | "done" | "card";

export interface SSEEvent {
  event: SSEEventType;
  data: Record<string, unknown>;
}

export const api = new ApiClient();
export { API_URL };
