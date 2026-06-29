/*
  chat/page.tsx — main study interface at /chat.

  URL parameters:
    ?mode=free|revision|deepdive|practice|lookup  (default: free)
    ?demo=true  triggers the demo mode banner

  Architecture:
    - Messages are stored in React state as a ChatMessage array
    - Sending a message creates a user entry then an empty assistant entry
    - The SSE stream updates the assistant entry token by token
    - The sidebar is toggled via sidebarOpen state
    - Session ID is generated once on mount and stored in a ref
    - AbortController cancels the current stream if the user sends
      a new message before the previous one finishes
*/

"use client";

import { useState, useRef, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { v4 as uuidv4 } from "uuid";

import Sidebar from "@/components/Sidebar";
import MessageBubble from "@/components/MessageBubble";
import { streamChat, quickLookup } from "@/lib/chat";
import { ChatMessage, StudyMode, ActiveMode, MetaEvent } from "@/lib/types";

const MODE_LABELS: Record<string, string> = {
  free:     "Free chat",
  revision: "Revision",
  deepdive: "Deep dive",
  practice: "Practice",
  lookup:   "Quick lookup",
};

// ── Inner component (needs useSearchParams, wrapped in Suspense below) ─────

function ChatInterface() {
  const searchParams  = useSearchParams();
  const initialMode   = (searchParams.get("mode") as StudyMode) || "free";
  const isDemoMode    = searchParams.get("demo") === "true";

  const [messages,     setMessages]     = useState<ChatMessage[]>([]);
  const [activeMode,   setActiveMode]   = useState<StudyMode>(initialMode);
  const [input,        setInput]        = useState("");
  const [isStreaming,  setIsStreaming]  = useState(false);
  const [sidebarOpen,  setSidebarOpen]  = useState(true);

  // Session ID persists for the lifetime of this component
  const sessionId      = useRef(uuidv4());
  // Cancels the in-flight SSE stream
  const abortRef       = useRef<AbortController | null>(null);
  // Ref to the messages container for auto-scroll
  const messagesEndRef = useRef<HTMLDivElement>(null);
  // Tracks recent queries for the sidebar
  const [recentQueries, setRecentQueries] = useState<string[]>([]);

  // Start sidebar collapsed on mobile
  useEffect(() => {
    if (window.innerWidth < 768) setSidebarOpen(false);
  }, []);

  // Auto-scroll to bottom whenever messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Send message ─────────────────────────────────────────────────────────

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || isStreaming) return;

    // Cancel any ongoing stream
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setInput("");
    setIsStreaming(true);

    // Unique IDs for this exchange
    const userMsgId = uuidv4();
    const aiMsgId   = uuidv4();

    // Add user message immediately
    setMessages(prev => [
      ...prev,
      { id: userMsgId, role: "user", content: text },
    ]);

    // Add empty assistant message — will fill with tokens
    setMessages(prev => [
      ...prev,
      { id: aiMsgId, role: "assistant", content: "", streaming: true },
    ]);

    // Track this query in the sidebar
    setRecentQueries(prev => [...prev, text]);

    // ── Quick Lookup — non-streaming JSON response ──────────────────────

    if (activeMode === "lookup") {
      try {
        const result = await quickLookup(text);
        const content = result.found
          ? result.definition ?? "No definition found."
          : result.message ?? "Not found in course materials.";

        setMessages(prev => prev.map(m =>
          m.id === aiMsgId
            ? {
                ...m,
                content,
                streaming:  false,
                confidence: result.found ? "High" : "Low",
                sources:    result.source ? [{ ...result.source, score: result.source.score }] : [],
              }
            : m
        ));
      } catch {
        setMessages(prev => prev.map(m =>
          m.id === aiMsgId
            ? { ...m, content: "Failed to reach the server.", streaming: false }
            : m
        ));
      }
      setIsStreaming(false);
      return;
    }

    // ── All other modes — SSE streaming ────────────────────────────────

    let streamingContent = "";

    await streamChat({
      message:   text,
      sessionId: sessionId.current,
      mode:      activeMode,
      signal:    abortRef.current.signal,

      onMeta: (event: MetaEvent) => {
        setMessages(prev => prev.map(m =>
          m.id === aiMsgId
            ? {
                ...m,
                confidence: event.confidence,
                sources:    event.sources,
                mode:       event.mode as ActiveMode,
              }
            : m
        ));
      },

      onToken: (token: string) => {
        streamingContent += token;
        // Functional update avoids stale closure over messages
        setMessages(prev => prev.map(m =>
          m.id === aiMsgId
            ? { ...m, content: streamingContent }
            : m
        ));
      },

      onDone: () => {
        setMessages(prev => prev.map(m =>
          m.id === aiMsgId ? { ...m, streaming: false } : m
        ));
        setIsStreaming(false);
      },

      onError: (error: string) => {
        setMessages(prev => prev.map(m =>
          m.id === aiMsgId
            ? { ...m, content: `Error: ${error}`, streaming: false }
            : m
        ));
        setIsStreaming(false);
      },
    });
  }, [input, isStreaming, activeMode]);

  // ── Submit on Enter (Shift+Enter for newline) ─────────────────────────

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const modeLabel = MODE_LABELS[activeMode] || "Free chat";

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-screen bg-teal-950">

      {/* ── Top bar ──────────────────────────────────────────────────── */}
      <header className="flex items-center gap-3 px-4 h-12
        border-b border-teal-800/50 bg-teal-900/60 flex-shrink-0">

        {/* Sidebar toggle */}
        <button
          onClick={() => setSidebarOpen(o => !o)}
          className="p-1.5 rounded-lg text-teal-500 hover:text-teal-300
            hover:bg-teal-800/60 transition-colors"
          aria-label="Toggle sidebar"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor"
            viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {/* Logo */}
        <Link href="/" className="text-sm font-medium text-teal-300
          hover:text-teal-100 transition-colors">
          Curra AI
        </Link>

        {/* Divider */}
        <span className="text-teal-700">·</span>

        {/* Active mode label */}
        <span className="text-xs text-teal-400 bg-teal-800/50
          border border-teal-700/50 px-2.5 py-1 rounded-full">
          {modeLabel}
        </span>

        {/* Demo badge */}
        {isDemoMode && (
          <>
            <span className="text-teal-700">·</span>
            <span className="text-[10px] text-rust-400 bg-rust-900/30
              border border-rust-800/40 px-2 py-0.5 rounded-full font-medium">
              Demo session
            </span>
          </>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Mode switcher link */}
        <Link
          href="/modes"
          className="text-xs text-teal-500 hover:text-teal-300
            transition-colors"
        >
          Switch mode
        </Link>
      </header>

      {/* ── Demo banner ───────────────────────────────────────────────── */}
      {isDemoMode && (
        <div className="flex items-center gap-3 px-4 py-2.5
          bg-rust-900/20 border-b border-rust-800/30">
          <svg className="w-3.5 h-3.5 text-rust-500 flex-shrink-0"
            fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894
              L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2
              2 0 002 2z" />
          </svg>
          <p className="text-[11px] text-rust-300">
            Demo session — responses are sourced exclusively from uploaded DAV course materials.{" "}
            <Link href="/demo" className="underline hover:text-rust-200">
              View lecturer dashboard →
            </Link>
          </p>
        </div>
      )}

      {/* ── Main body — sidebar + messages ───────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* Sidebar */}
        <Sidebar
          isOpen={sidebarOpen}
          activeMode={activeMode}
          onModeChange={setActiveMode}
          recentQueries={recentQueries}
        />

        {/* Chat area */}
        <div className="flex flex-col flex-1 overflow-hidden">

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-6">
            {messages.length === 0 ? (
              <EmptyState mode={activeMode} modeLabel={modeLabel} />
            ) : (
              <div className="max-w-2xl mx-auto flex flex-col gap-5">
                {messages.map(msg => (
                  <MessageBubble key={msg.id} message={msg} />
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input bar */}
          <div className="flex-shrink-0 px-6 py-4
            border-t border-teal-800/40 bg-teal-900/30">
            <div className="max-w-2xl mx-auto flex gap-3 items-end">
              <textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  activeMode === "lookup"
                    ? "Type a term to look up..."
                    : `Ask a ${modeLabel.toLowerCase()} question...`
                }
                rows={1}
                className="flex-1 bg-teal-800/40 border border-teal-700/50
                  rounded-xl px-4 py-3 text-sm text-teal-100 placeholder-teal-600
                  outline-none focus:border-teal-600 focus:ring-1
                  focus:ring-teal-600/30 resize-none transition-colors
                  min-h-[44px] max-h-32"
                style={{ height: "auto" }}
                onInput={e => {
                  const t = e.target as HTMLTextAreaElement;
                  t.style.height = "auto";
                  t.style.height = `${Math.min(t.scrollHeight, 128)}px`;
                }}
                disabled={isStreaming}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isStreaming}
                className="w-10 h-10 flex items-center justify-center
                  rounded-xl bg-teal-600 hover:bg-teal-500 disabled:opacity-30
                  disabled:cursor-not-allowed transition-colors flex-shrink-0"
                aria-label="Send message"
              >
                {isStreaming ? (
                  <svg className="w-4 h-4 text-teal-100 animate-spin"
                    fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10"
                      stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-teal-100" fill="none"
                    stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round"
                      strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                  </svg>
                )}
              </button>
            </div>
            <p className="text-center text-[10px] text-teal-700 mt-2">
              Answers sourced from uploaded DAV materials only · Enter to send
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Empty state shown before first message ─────────────────────────────────

function EmptyState({ mode, modeLabel }: { mode: StudyMode; modeLabel: string }) {
  const HINTS: Record<StudyMode, string[]> = {
    free:     ["What is data cleaning?", "Explain the five steps of the analytics process", "What tools are used in data analytics?"],
    revision: ["I have an exam in 2 weeks and I'm not confident about data visualisation"],
    deepdive: ["Take me through data acquisition completely"],
    practice: ["Give me a practice question on descriptive analytics"],
    lookup:   ["data wrangling", "cosine similarity", "descriptive analytics"],
  };

  return (
    <div className="flex flex-col items-center justify-center h-full
      text-center px-8">
      <div className="w-10 h-10 rounded-xl bg-teal-800/60 border
        border-teal-700/50 flex items-center justify-center mb-4">
        <svg className="w-5 h-5 text-teal-500" fill="none"
          stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0
            012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      </div>
      <h2 className="text-sm font-medium text-teal-200 mb-1">{modeLabel}</h2>
      <p className="text-xs text-teal-500 mb-6 max-w-xs">
        {mode === "lookup"
          ? "Type any term from your DAV slides for an instant definition."
          : "Ask a question about your DAV course materials."}
      </p>
      <div className="flex flex-col gap-2 w-full max-w-sm">
        {HINTS[mode]?.map((hint, i) => (
          <div key={i} className="text-xs text-teal-400 bg-teal-800/30
            border border-teal-700/30 rounded-lg px-4 py-2.5 text-left
            cursor-default">
            {hint}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Suspense wrapper required for useSearchParams ──────────────────────────

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center bg-teal-950">
        <div className="w-5 h-5 border-2 border-teal-700 border-t-teal-400
          rounded-full animate-spin" />
      </div>
    }>
      <ChatInterface />
    </Suspense>
  );
}