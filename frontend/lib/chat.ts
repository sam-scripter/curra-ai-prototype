/*
  chat.ts — SSE streaming client for /api/chat.
  
  The backend sends Server-Sent Events in this format:
    data: {"type": "meta", "confidence": "High", "sources": [...], "mode": "free"}
    data: {"type": "token", "content": "Data"}
    data: {"type": "token", "content": " cleaning"}
    ...
    data: {"type": "done"}
  
  We use fetch() + ReadableStream rather than EventSource because:
    1. EventSource only supports GET requests
    2. Our /api/chat endpoint is POST
    3. fetch() gives us an AbortController for cleanup
*/

import { MetaEvent, TokenEvent, ActiveMode } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface StreamChatParams {
  message:    string;
  sessionId:  string;
  mode:       string;
  signal:     AbortSignal;  // Used to cancel the stream when the component unmounts
  onMeta:     (event: MetaEvent) => void;
  onToken:    (token: string) => void;
  onDone:     () => void;
  onError:    (error: string) => void;
}

export async function streamChat({
  message,
  sessionId,
  mode,
  signal,
  onMeta,
  onToken,
  onDone,
  onError,
}: StreamChatParams): Promise<void> {
  try {
    const response = await fetch(`${API_URL}/api/chat`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        message,
        session_id: sessionId,
        mode,
      }),
      signal,
    });

    if (!response.ok) {
      onError(`Server error: ${response.status}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      onError("No response body");
      return;
    }

    const decoder = new TextDecoder();
    // Buffer holds partial lines between chunk boundaries.
    // A single network chunk may contain multiple events, or
    // an event may be split across two chunks.
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Split on newlines. The last element may be an incomplete line
      // — keep it in the buffer for the next iteration.
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;

        const raw = line.slice(6).trim();
        if (!raw) continue;

        try {
          const event = JSON.parse(raw);
          if (event.type === "meta")  onMeta(event);
          if (event.type === "token") onToken(event.content);
          if (event.type === "done")  onDone();
        } catch {
          // Malformed JSON in a single event — skip it, don't crash
        }
      }
    }
  } catch (error: unknown) {
    // AbortError is expected when the user navigates away or sends a new
    // message before the current one finishes. Don't treat it as an error.
    if (error instanceof Error && error.name === "AbortError") return;
    onError(error instanceof Error ? error.message : "Unknown error");
  }
}


// ── Quick Lookup — non-streaming JSON endpoint ─────────────────────────────

export interface LookupResult {
  term:        string;
  definition:  string | null;
  found:       boolean;
  message?:    string;
  source?: {
    filename:    string;
    page_number: number;
    score:       number;
  };
}

export async function quickLookup(term: string): Promise<LookupResult> {
  const response = await fetch(
    `${API_URL}/api/lookup?term=${encodeURIComponent(term)}`
  );
  if (!response.ok) throw new Error(`Lookup failed: ${response.status}`);
  return response.json();
}