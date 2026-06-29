/*
  SourceCitations.tsx — collapsible list of source chunks cited in an answer.
  
  Shows the filename and page number for each retrieved chunk.
  Collapsed by default to keep the chat clean — one click to expand.
  The similarity score is shown in muted text for transparency.
*/

"use client";

import { useState } from "react";
import { Source } from "@/lib/types";

interface SourceCitationsProps {
  sources: Source[];
}

export default function SourceCitations({ sources }: SourceCitationsProps) {
  const [open, setOpen] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-teal-800/50">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-[11px] text-teal-400
          hover:text-teal-300 transition-colors"
      >
        {/* Chevron rotates when expanded */}
        <svg
          className={`w-3 h-3 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M19 9l-7 7-7-7" />
        </svg>
        {sources.length} source{sources.length !== 1 ? "s" : ""} cited
      </button>

      {open && (
        <div className="mt-2 flex flex-col gap-1">
          {sources.map((source, i) => (
            <div
              key={i}
              className="flex items-center gap-2 text-[11px] text-teal-400/80"
            >
              {/* Small document icon */}
              <svg className="w-3 h-3 text-teal-600 flex-shrink-0"
                fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586
                    a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2
                    2 0 01-2 2z" />
              </svg>
              <span className="truncate flex-1">
                {source.filename}, Page {source.page_number}
              </span>
              <span className="text-teal-700 flex-shrink-0">
                {(source.score * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}