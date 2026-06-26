/*
  modes/page.tsx — mode selection page, served at /modes.
  
  Displays all five study modes as clickable cards. Each card links
  to the chat page with a mode query parameter (?mode=revision etc.)
  which the chat interface will use in Phase 5 to configure its behaviour.
  
  At prototype stage this is a static page. In Phase 5 it becomes
  the main entry point users land on after opening the app.
*/

import Link from "next/link";

/*
  MODES array — the single source of truth for mode metadata.
  
  If we need to add, rename, or reorder a mode, we change it here
  and the UI updates automatically. The href for each mode passes
  the mode as a URL query parameter so the chat page knows which
  mode was selected.
*/
const MODES = [
  {
    name: "Free Chat",
    description: "Ask any question about the course. Best for targeted queries when you know exactly what you want.",
    href: "/chat?mode=free",
    badge: "Default",
  },
  {
    name: "Revision Mode",
    description: "Structured exam prep. The AI builds a prioritised revision plan based on your timeline and confidence.",
    href: "/chat?mode=revision",
    badge: null,
  },
  {
    name: "Topic Deep Dive",
    description: "Select one topic and the AI covers it end to end — from fundamentals through to application.",
    href: "/chat?mode=deepdive",
    badge: null,
  },
  {
    name: "Practice Mode",
    description: "Past paper questions one at a time with AI feedback against the course materials.",
    href: "/chat?mode=practice",
    badge: null,
  },
  {
    name: "Quick Lookup",
    description: "Type a term and get a concise definition sourced directly from your slides with a citation.",
    href: "/chat?mode=lookup",
    badge: "Fastest",
  },
];

export default function ModesPage() {
  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      
      {/* Page header */}
      <div className="mb-8">
        <Link href="/" className="text-indigo-400 text-sm hover:text-indigo-300 transition-colors">
          ← Back
        </Link>
        <h1 className="text-3xl font-bold mt-4 mb-2">Choose a Study Mode</h1>
        <p className="text-gray-400">Each mode is designed for a different kind of study session.</p>
      </div>

      {/* 
        Mode cards grid.
        grid-cols-1 on mobile, 2 columns on medium screens and up.
      */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {MODES.map((mode) => (
          <Link
            key={mode.name}
            href={mode.href}
            className="block p-6 bg-gray-900 border border-gray-800 rounded-xl hover:border-indigo-500 transition-colors group"
          >
            {/* Mode name and optional badge */}
            <div className="flex items-center justify-between mb-2">
              <h2 className="font-semibold text-white group-hover:text-indigo-300 transition-colors">
                {mode.name}
              </h2>
              {mode.badge && (
                <span className="text-xs px-2 py-0.5 bg-indigo-900 text-indigo-300 rounded-full">
                  {mode.badge}
                </span>
              )}
            </div>
            {/* Mode description */}
            <p className="text-sm text-gray-400">{mode.description}</p>
          </Link>
        ))}
      </div>

    </main>
  );
}