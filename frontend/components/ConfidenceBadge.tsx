/*
  ConfidenceBadge.tsx — displays the confidence level of an AI response.
  
  Three states with distinct colors:
    High   → green  — strong match in knowledge base, answer is reliable
    Medium → amber  — partial match, answer is reasonable but may be incomplete
    Low    → red    — weak match, topic likely not covered in uploaded materials
  
  Shown inline in the message header alongside the AI avatar and name.
*/

import { ConfidenceLevel } from "@/lib/types";

interface ConfidenceBadgeProps {
  level: ConfidenceLevel;
}

const STYLES: Record<ConfidenceLevel, string> = {
  High:   "bg-emerald-950 text-emerald-400 border-emerald-800",
  Medium: "bg-amber-950 text-amber-400 border-amber-800",
  Low:    "bg-red-950 text-red-400 border-red-900",
};

const DOTS: Record<ConfidenceLevel, string> = {
  High:   "bg-emerald-400",
  Medium: "bg-amber-400",
  Low:    "bg-red-400",
};

export default function ConfidenceBadge({ level }: ConfidenceBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-[10px] font-medium
        px-2 py-0.5 rounded-full border ${STYLES[level]}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${DOTS[level]}`} />
      {level} confidence
    </span>
  );
}