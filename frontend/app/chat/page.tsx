/*
  chat/page.tsx — chat interface, served at /chat.
  
  This is the main study interface where all five modes ultimately land.
  The active mode is read from the URL query parameter (?mode=free etc.)
  
  At prototype stage (Phase 1), this is a static placeholder shell —
  the input is disabled, messages don't send, and no API is called.
  The full interactive implementation is built in Phase 5 once the
  backend RAG pipeline (Phases 2-4) is complete.
  
  The structure is already correct for Phase 5:
  - fixed header with mode indicator
  - scrollable message area in the middle
  - fixed input bar at the bottom
  This layout won't change — only the interactivity gets added later.
*/

"use client";

/*
  "use client" marks this as a Client Component.
  
  In Next.js App Router, components are Server Components by default —
  they render on the server and send plain HTML to the browser.
  
  We need "use client" here because:
  1. We read URL search params (useSearchParams hook requires the browser)
  2. In Phase 5 we'll manage message state with useState
  3. We'll handle keyboard events (Enter to send)
  
  Any component that uses React hooks or browser APIs must be a Client Component.
*/

import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense } from "react";

/*
  MODE_LABELS maps the URL parameter value to a human-readable label
  shown in the top bar. Keeping this separate from the MODES array
  in modes/page.tsx avoids an import dependency between pages.
*/
const MODE_LABELS: Record<string, string> = {
  free:     "Free Chat",
  revision: "Revision Mode",
  deepdive: "Topic Deep Dive",
  practice: "Practice Mode",
  lookup:   "Quick Lookup",
};

function ChatInterface() {
  /*
    useSearchParams reads the current URL's query string.
    ?mode=revision → searchParams.get("mode") returns "revision"
    If no mode param is present, we default to "free".
  */
  const searchParams = useSearchParams();
  const mode = searchParams.get("mode") ?? "free";
  const modeLabel = MODE_LABELS[mode] ?? "Free Chat";

  return (
    <main className="flex flex-col h-screen">

      {/* 
        Top bar — fixed height, always visible.
        Shows the product name, current mode, and a link back to mode selection.
      */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-950 shrink-0">
        <Link href="/" className="text-indigo-400 font-semibold text-sm hover:text-indigo-300 transition-colors">
          Curra AI
        </Link>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400 bg-gray-800 px-3 py-1 rounded-full">
            {modeLabel}
          </span>
          <Link
            href="/modes"
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            Switch mode
          </Link>
        </div>
      </header>

      {/* 
        Message area — fills remaining vertical space between header and input bar.
        overflow-y-auto allows it to scroll when messages overflow.
        In Phase 5 this will render the actual conversation messages.
      */}
      <div className="flex-1 overflow-y-auto p-6 flex items-center justify-center">
        <div className="text-center text-gray-700">
          <p className="text-lg mb-2">Ready to study</p>
          <p className="text-sm">
            Chat interface builds in Phase 5. Backend RAG pipeline first.
          </p>
        </div>
      </div>

      {/* 
        Input bar — fixed to the bottom.
        shrink-0 prevents it from being compressed when the message area is full.
        In Phase 5 this becomes the active send interface.
      */}
      <div className="shrink-0 p-4 border-t border-gray-800 bg-gray-950">
        <div className="flex gap-3 max-w-3xl mx-auto">
          <input
            type="text"
            placeholder={`Ask a ${modeLabel} question...`}
            className="flex-1 bg-gray-800 rounded-lg px-4 py-3 text-sm outline-none 
                       focus:ring-2 focus:ring-indigo-500 text-gray-500 cursor-not-allowed"
            disabled
          />
          <button
            className="px-5 py-3 bg-indigo-600 rounded-lg text-sm font-medium 
                       opacity-40 cursor-not-allowed"
            disabled
          >
            Send
          </button>
        </div>
      </div>

    </main>
  );
}

/*
  Suspense wrapper is required by Next.js when using useSearchParams
  in a Client Component. Without it, the build will throw a warning
  about the component not being wrapped in a Suspense boundary.
  
  Suspense defines what to show while the component is loading —
  in this case a simple loading state that matches the dark background.
*/
export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center bg-gray-950 text-gray-600">
        Loading...
      </div>
    }>
      <ChatInterface />
    </Suspense>
  );
}