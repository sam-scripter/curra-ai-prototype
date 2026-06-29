/*
  types.ts — shared TypeScript interfaces for the Curra AI frontend.
  
  All types for messages, API responses, and study modes are defined here.
  Import from this file throughout the app rather than redefining locally.
*/

// ── Study modes ────────────────────────────────────────────────────────────

export type StudyMode =
  | "free"
  | "revision"
  | "deepdive"
  | "practice"
  | "lookup";

// Mode keys including Socratic variants (set by the backend, never chosen by the student)
export type ActiveMode =
  | StudyMode
  | "socratic"
  | "socratic_video"
  | "code_guide";

// ── Source citations ───────────────────────────────────────────────────────

export interface Source {
  filename:    string;
  page_number: number;
  score:       number;
}

// ── Confidence ─────────────────────────────────────────────────────────────

export type ConfidenceLevel = "High" | "Medium" | "Low";

// ── Chat messages ──────────────────────────────────────────────────────────

export interface ChatMessage {
  id:          string;
  role:        "user" | "assistant";
  content:     string;
  // Only present on assistant messages
  confidence?: ConfidenceLevel;
  sources?:    Source[];
  mode?:       ActiveMode;
  // True while tokens are still streaming in
  streaming?:  boolean;
}

// ── SSE events from /api/chat ──────────────────────────────────────────────

export interface MetaEvent {
  type:       "meta";
  confidence: ConfidenceLevel;
  sources:    Source[];
  mode:       ActiveMode;
}

export interface TokenEvent {
  type:    "token";
  content: string;
}

export interface DoneEvent {
  type: "done";
}

export type SSEEvent = MetaEvent | TokenEvent | DoneEvent;