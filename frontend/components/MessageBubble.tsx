/*
  MessageBubble.tsx — renders one message in the chat thread.
  
  User messages: right-aligned teal bubble.
  
  Assistant messages: full-width card with:
    - Avatar + name + confidence badge in the header
    - Amber left border if mode is socratic/socratic_video/code_guide
    - "Guided mode" tag for Socratic responses
    - Markdown-rendered answer body (via react-markdown)
    - Blinking cursor while streaming
    - Collapsible source citations at the bottom
    - Low confidence gap notice
*/

import ReactMarkdown from "react-markdown";
import ConfidenceBadge from "./ConfidenceBadge";
import SourceCitations from "./SourceCitations";
import { ChatMessage } from "@/lib/types";

interface MessageBubbleProps {
  message: ChatMessage;
}

// These modes trigger the Socratic amber indicator
const SOCRATIC_MODES = new Set(["socratic", "socratic_video", "code_guide"]);

const SOCRATIC_LABELS: Record<string, string> = {
  socratic:       "Class exercise — guided mode",
  socratic_video: "Video activity — guided mode",
  code_guide:     "Programming exercise — guided mode",
};

export default function MessageBubble({ message }: MessageBubbleProps) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div
          className="max-w-[72%] bg-teal-700 text-teal-50 px-4 py-2.5
            rounded-2xl rounded-br-sm text-sm leading-relaxed"
        >
          {message.content}
        </div>
      </div>
    );
  }

  // Assistant message
  const isSocratic = message.mode && SOCRATIC_MODES.has(message.mode);
  const socraticLabel = message.mode ? SOCRATIC_LABELS[message.mode] : null;

  return (
    <div className="flex flex-col gap-2">
      {/* Message header — avatar, name, confidence */}
      <div className="flex items-center gap-2">
        {/* AI avatar */}
        <div
          className="w-6 h-6 rounded-full bg-teal-800 border border-teal-600
            flex items-center justify-center flex-shrink-0"
        >
          <svg className="w-3 h-3 text-teal-400" fill="none"
            stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M5 3l14 9-14 9V3z" />
          </svg>
        </div>
        <span className="text-xs font-medium text-teal-300">Curra AI</span>
        {message.confidence && !message.streaming && (
          <ConfidenceBadge level={message.confidence} />
        )}
        {message.streaming && (
          <span className="text-[10px] text-teal-600 animate-pulse">
            thinking...
          </span>
        )}
      </div>

      {/* Message body */}
      <div
        className={`rounded-2xl rounded-tl-sm p-4 text-sm
          bg-teal-900/60 border ${
          isSocratic
            // Socratic mode: amber left border, slightly different surface
            ? "border-l-2 border-l-rust-600 border-t-teal-800/50 border-r-teal-800/50 border-b-teal-800/50"
            : "border-teal-800/40"
        }`}
      >
        {/* Socratic mode tag */}
        {isSocratic && socraticLabel && !message.streaming && (
          <div
            className="inline-flex items-center gap-1.5 text-[10px] font-medium
              text-rust-400 bg-rust-900/40 border border-rust-800/50
              px-2 py-0.5 rounded-full mb-3"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor"
              viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168
                5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477
                4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0
                3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5
                18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            {socraticLabel}
          </div>
        )}

        {/* Answer content — rendered as markdown */}
        <div className="prose-curra">
          <ReactMarkdown>{message.content}</ReactMarkdown>
          {/* Blinking cursor shown while streaming */}
          {message.streaming && (
            <span className="inline-block w-0.5 h-4 bg-teal-400
              animate-pulse ml-0.5 align-middle" />
          )}
        </div>

        {/* Low confidence gap notice */}
        {message.confidence === "Low" && !message.streaming && (
          <div
            className="mt-3 flex items-center gap-2 text-[11px] text-red-400
              bg-red-950/40 border border-red-900/50 rounded-lg px-3 py-2"
          >
            <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none"
              stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667
                1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34
                16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            This topic is not well covered in the uploaded materials. Query logged.
          </div>
        )}

        {/* Source citations — only shown when streaming is complete */}
        {!message.streaming && message.sources && message.sources.length > 0 && (
          <SourceCitations sources={message.sources} />
        )}
      </div>
    </div>
  );
}