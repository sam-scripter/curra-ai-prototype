/*
  Sidebar.tsx — collapsible study mode navigation.
  
  Displays the five study modes and recent session questions.
  The parent (chat page) controls open/closed state via isOpen prop.
  On screens below 768px the parent starts it closed.
  
  When a mode is selected, it calls onModeChange. Navigating between
  modes does not reset the current session — it changes the system
  prompt for the next message only.
*/

import Link from "next/link";
import { StudyMode } from "@/lib/types";

interface SidebarProps {
  isOpen:         boolean;
  activeMode:     StudyMode;
  onModeChange:   (mode: StudyMode) => void;
  recentQueries:  string[];
}

const MODES: { key: StudyMode; label: string; description: string }[] = [
  { key: "free",      label: "Free chat",   description: "Ask anything" },
  { key: "revision",  label: "Revision",    description: "Structured prep" },
  { key: "deepdive",  label: "Deep dive",   description: "One topic, fully" },
  { key: "practice",  label: "Practice",    description: "Past questions" },
  { key: "lookup",    label: "Quick lookup",description: "Fast definitions" },
];

export default function Sidebar({
  isOpen,
  activeMode,
  onModeChange,
  recentQueries,
}: SidebarProps) {
  if (!isOpen) return null;

  return (
    <aside
      className="w-52 flex-shrink-0 border-r border-teal-800/40
        bg-teal-900/50 flex flex-col overflow-hidden"
    >
      {/* Study modes */}
      <div className="p-3 pt-4">
        <p className="text-[10px] text-teal-600 uppercase tracking-widest
          font-medium mb-2 px-2">
          Study modes
        </p>
        <nav className="flex flex-col gap-0.5">
          {MODES.map((mode) => {
            const isActive = activeMode === mode.key;
            return (
              <button
                key={mode.key}
                onClick={() => onModeChange(mode.key)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm
                  transition-colors border-l-2 ${
                  isActive
                    ? "bg-teal-700/40 text-teal-100 border-teal-500"
                    : "text-teal-300 border-transparent hover:bg-teal-800/40 hover:text-teal-100"
                }`}
              >
                <div className="font-medium text-[12px]">{mode.label}</div>
                <div className={`text-[10px] mt-0.5 ${
                  isActive ? "text-teal-300" : "text-teal-500"
                }`}>
                  {mode.description}
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Divider */}
      <div className="mx-4 border-t border-teal-800/40 my-1" />

      {/* Recent questions */}
      {recentQueries.length > 0 && (
        <div className="p-3 flex-1 overflow-y-auto">
          <p className="text-[10px] text-teal-600 uppercase tracking-widest
            font-medium mb-2 px-2">
            This session
          </p>
          <div className="flex flex-col gap-0.5">
            {recentQueries.slice(-8).reverse().map((q, i) => (
              <div
                key={i}
                className="px-3 py-1.5 text-[11px] text-teal-400
                  truncate hover:text-teal-200 transition-colors cursor-default"
                title={q}
              >
                {q}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bottom link to demo dashboard */}
      <div className="p-3 border-t border-teal-800/40">
        <Link
          href="/demo"
          className="flex items-center gap-2 px-3 py-2 rounded-lg
            text-[11px] text-teal-500 hover:text-teal-300 hover:bg-teal-800/40
            transition-colors"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor"
            viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2
              2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002
              2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0
              01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Lecturer dashboard
        </Link>
      </div>
    </aside>
  );
}