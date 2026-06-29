/*
  modes/page.tsx — study mode selection at /modes.

  Five mode cards, each describing what the mode is for.
  Clicking a card routes to /chat with the mode as a URL parameter.
  The chat page reads this parameter and sets the active mode.
*/

import Link from "next/link";

const MODES = [
  {
    key:         "free",
    label:       "Free chat",
    description: "Ask any question about DAV. Best when you know exactly what you want to understand.",
    badge:       "Default",
    badgeColor:  "bg-teal-800/60 text-teal-300 border-teal-700",
    icon: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
        d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863
        9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3
        12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    ),
  },
  {
    key:         "revision",
    label:       "Revision mode",
    description: "Structured exam preparation. The AI builds a prioritised plan from your timeline and confidence level.",
    badge:       null,
    badgeColor:  "",
    icon: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0
        00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2
        0 012 2m-6 9l2 2 4-4" />
    ),
  },
  {
    key:         "deepdive",
    label:       "Topic deep dive",
    description: "Select one topic and cover it completely — definition, key concepts, examples, and limitations.",
    badge:       null,
    badgeColor:  "",
    icon: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
    ),
  },
  {
    key:         "practice",
    label:       "Practice mode",
    description: "Past paper questions presented one at a time. Submit your answer and get graded feedback from the course materials.",
    badge:       null,
    badgeColor:  "",
    icon: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
        d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536
        3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
    ),
  },
  {
    key:         "lookup",
    label:       "Quick lookup",
    description: "Type a term, get a precise definition sourced from your slides with a page citation.",
    badge:       "Fastest",
    badgeColor:  "bg-rust-900/40 text-rust-400 border-rust-800/50",
    icon: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
        d="M13 10V3L4 14h7v7l9-11h-7z" />
    ),
  },
];

export default function ModesPage() {
  return (
    <main className="min-h-screen bg-teal-950 p-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/"
            className="text-teal-500 text-sm hover:text-teal-300
              transition-colors inline-flex items-center gap-1 mb-6"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor"
              viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </Link>
          <h1 className="text-2xl font-medium text-teal-100 mb-2">
            Choose a study mode
          </h1>
          <p className="text-teal-400 text-sm">
            Each mode is designed for a different kind of session.
          </p>
        </div>

        {/* Mode cards */}
        <div className="flex flex-col gap-3">
          {MODES.map((mode) => (
            <Link
              key={mode.key}
              href={`/chat?mode=${mode.key}`}
              className="group flex items-start gap-4 p-4 rounded-xl
                bg-teal-900/40 border border-teal-800/40
                hover:border-teal-600/60 hover:bg-teal-800/40
                transition-all"
            >
              {/* Icon */}
              <div className="w-9 h-9 rounded-lg bg-teal-800 border
                border-teal-700 flex items-center justify-center flex-shrink-0
                group-hover:border-teal-600 transition-colors">
                <svg className="w-4 h-4 text-teal-400" fill="none"
                  stroke="currentColor" viewBox="0 0 24 24">
                  {mode.icon}
                </svg>
              </div>

              {/* Label + description */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-teal-100
                    group-hover:text-white transition-colors">
                    {mode.label}
                  </span>
                  {mode.badge && (
                    <span className={`text-[10px] px-2 py-0.5 rounded-full
                      border font-medium ${mode.badgeColor}`}>
                      {mode.badge}
                    </span>
                  )}
                </div>
                <p className="text-xs text-teal-400 leading-relaxed">
                  {mode.description}
                </p>
              </div>

              {/* Arrow */}
              <svg className="w-4 h-4 text-teal-700 group-hover:text-teal-400
                transition-colors flex-shrink-0 mt-0.5" fill="none"
                stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round"
                  strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}