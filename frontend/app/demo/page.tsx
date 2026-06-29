/*
  demo/page.tsx — Lecturer demo dashboard at /demo.

  Read-only analytics view designed to be shown to the DAV lecturer
  during the prototype demonstration. Shows:
    - Stat cards: documents, chunks, queries, gaps
    - Confidence distribution bar
    - Ingested documents table
    - Knowledge gap log

  Polls the backend every 30 seconds so live queries during the demo
  update the stats without a manual refresh.

  No authentication in the prototype — URL is the only access control.
*/

"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Types ──────────────────────────────────────────────────────────────────

interface Stats {
  documents:            number;
  total_chunks:         number;
  total_queries:        number;
  gaps_logged:          number;
  confidence_breakdown: { High: number; Medium: number; Low: number };
}

interface DocRecord {
  id:          number;
  filename:    string;
  chunk_count: number;
  uploaded_at: string | null;
}

interface GapRecord {
  id:         number;
  query:      string;
  confidence: number;
  asked_at:   string | null;
}

// ── Helpers ────────────────────────────────────────────────────────────────

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-KE", {
    day:    "2-digit",
    month:  "short",
    hour:   "2-digit",
    minute: "2-digit",
  });
}

// ── Sub-components ─────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  sub,
  accent = false,
}: {
  label:   string;
  value:   number | string;
  sub?:    string;
  accent?: boolean;
}) {
  return (
    <div className={`rounded-xl p-4 border ${
      accent
        ? "bg-rust-900/20 border-rust-800/40"
        : "bg-teal-800/30 border-teal-700/40"
    }`}>
      <p className="text-[11px] text-teal-500 uppercase tracking-widest mb-1">
        {label}
      </p>
      <p className={`text-2xl font-medium ${
        accent ? "text-rust-400" : "text-teal-100"
      }`}>
        {value}
      </p>
      {sub && (
        <p className="text-[11px] text-teal-600 mt-1">{sub}</p>
      )}
    </div>
  );
}

function ConfidenceBar({ breakdown, total }: {
  breakdown: { High: number; Medium: number; Low: number };
  total:     number;
}) {
  if (total === 0) {
    return (
      <p className="text-xs text-teal-600">
        No queries yet — ask a question in the chat to see the breakdown.
      </p>
    );
  }

  const pct = (n: number) =>
    total > 0 ? Math.round((n / total) * 100) : 0;

  const highPct   = pct(breakdown.High);
  const mediumPct = pct(breakdown.Medium);
  const lowPct    = pct(breakdown.Low);

  return (
    <div className="space-y-3">
      {/* Stacked bar */}
      <div className="flex h-3 rounded-full overflow-hidden gap-0.5">
        {highPct > 0 && (
          <div
            className="bg-emerald-500 rounded-full transition-all"
            style={{ width: `${highPct}%` }}
          />
        )}
        {mediumPct > 0 && (
          <div
            className="bg-amber-500 rounded-full transition-all"
            style={{ width: `${mediumPct}%` }}
          />
        )}
        {lowPct > 0 && (
          <div
            className="bg-red-500 rounded-full transition-all"
            style={{ width: `${lowPct}%` }}
          />
        )}
      </div>

      {/* Legend */}
      <div className="flex gap-6">
        {[
          { label: "High",   count: breakdown.High,   pct: highPct,   color: "bg-emerald-500", text: "text-emerald-400" },
          { label: "Medium", count: breakdown.Medium, pct: mediumPct, color: "bg-amber-500",   text: "text-amber-400"   },
          { label: "Low",    count: breakdown.Low,    pct: lowPct,    color: "bg-red-500",     text: "text-red-400"     },
        ].map(item => (
          <div key={item.label} className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${item.color}`} />
            <span className={`text-xs ${item.text}`}>
              {item.label}
            </span>
            <span className="text-xs text-teal-600">
              {item.count} ({item.pct}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main dashboard ─────────────────────────────────────────────────────────

export default function DemoPage() {
  const [stats,     setStats]     = useState<Stats | null>(null);
  const [documents, setDocuments] = useState<DocRecord[]>([]);
  const [gaps,      setGaps]      = useState<GapRecord[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [lastSync,  setLastSync]  = useState<Date | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      const [statsRes, docsRes, gapsRes] = await Promise.all([
        fetch(`${API_URL}/api/demo/stats`),
        fetch(`${API_URL}/api/demo/documents`),
        fetch(`${API_URL}/api/demo/gaps`),
      ]);

      const [statsData, docsData, gapsData] = await Promise.all([
        statsRes.json(),
        docsRes.json(),
        gapsRes.json(),
      ]);

      setStats(statsData);
      setDocuments(docsData.documents ?? []);
      setGaps(gapsData.gaps ?? []);
      setLastSync(new Date());
    } catch (err) {
      console.error("Demo dashboard fetch failed:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch + poll every 30 seconds
  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30_000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  // ── Render ──────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-teal-950">
        <div className="w-5 h-5 border-2 border-teal-700 border-t-teal-400
          rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-teal-950 px-6 py-8">
      <div className="max-w-4xl mx-auto">

        {/* ── Header ─────────────────────────────────────────────────── */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] text-rust-400 bg-rust-900/30
                border border-rust-800/40 px-2 py-0.5 rounded-full font-medium
                uppercase tracking-widest">
                Lecturer dashboard
              </span>
            </div>
            <h1 className="text-xl font-medium text-teal-100 mt-2">
              Curra AI — Knowledge Base Overview
            </h1>
            <p className="text-sm text-teal-400 mt-1">
              Data Analytics and Visualisation · Strathmore University MSc IT
            </p>
          </div>
          <div className="text-right">
            <Link
              href="/chat?demo=true"
              className="inline-flex items-center gap-1.5 text-xs text-teal-400
                bg-teal-800/40 border border-teal-700/40 px-3 py-2 rounded-lg
                hover:border-teal-600 hover:text-teal-200 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor"
                viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9
                  8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512
                  15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              Open live chat
            </Link>
            {lastSync && (
              <p className="text-[10px] text-teal-700 mt-2">
                Last updated {lastSync.toLocaleTimeString()} · auto-refreshes every 30s
              </p>
            )}
          </div>
        </div>

        {/* ── Stat cards ──────────────────────────────────────────────── */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
            <StatCard
              label="Documents"
              value={stats.documents}
              sub="lecture files ingested"
            />
            <StatCard
              label="Text chunks"
              value={stats.total_chunks}
              sub="searchable segments"
            />
            <StatCard
              label="Queries"
              value={stats.total_queries}
              sub="questions asked"
            />
            <StatCard
              label="Gaps logged"
              value={stats.gaps_logged}
              sub="unanswered questions"
              accent={stats.gaps_logged > 0}
            />
          </div>
        )}

        {/* ── Confidence breakdown ─────────────────────────────────────── */}
        {stats && stats.total_queries > 0 && (
          <div className="rounded-xl bg-teal-800/20 border border-teal-700/40
            p-5 mb-6">
            <h2 className="text-sm font-medium text-teal-200 mb-4">
              Answer confidence distribution
            </h2>
            <ConfidenceBar
              breakdown={stats.confidence_breakdown}
              total={stats.total_queries}
            />
            <p className="text-[11px] text-teal-600 mt-3">
              High: strong match in materials · Medium: partial match ·
              Low: topic not covered — logged as a gap
            </p>
          </div>
        )}

        {/* ── Ingested documents ───────────────────────────────────────── */}
        <div className="rounded-xl bg-teal-800/20 border border-teal-700/40
          p-5 mb-6">
          <h2 className="text-sm font-medium text-teal-200 mb-4">
            Knowledge base — ingested documents
          </h2>
          {documents.length === 0 ? (
            <p className="text-xs text-teal-600">
              No documents ingested yet.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-teal-700/40">
                    <th className="text-left text-teal-500 font-medium pb-2 pr-4">
                      File
                    </th>
                    <th className="text-right text-teal-500 font-medium pb-2 pr-4">
                      Chunks
                    </th>
                    <th className="text-right text-teal-500 font-medium pb-2">
                      Ingested
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr
                      key={doc.id}
                      className="border-b border-teal-800/30 last:border-0"
                    >
                      <td className="py-2.5 pr-4 text-teal-200 max-w-xs truncate">
                        <div className="flex items-center gap-2">
                          <svg className="w-3 h-3 text-teal-600 flex-shrink-0"
                            fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round"
                              strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0
                              01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414
                              5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          {doc.filename}
                        </div>
                      </td>
                      <td className="py-2.5 pr-4 text-right text-teal-400">
                        {doc.chunk_count}
                      </td>
                      <td className="py-2.5 text-right text-teal-600">
                        {formatDate(doc.uploaded_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* ── Gap log ─────────────────────────────────────────────────── */}
        <div className="rounded-xl bg-rust-900/10 border border-rust-800/30 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-medium text-teal-200">
                Knowledge gap log
              </h2>
              <p className="text-[11px] text-teal-500 mt-0.5">
                Questions students asked that the uploaded materials
                couldn&apos;t answer
              </p>
            </div>
            {gaps.length > 0 && (
              <span className="text-xs text-rust-400 bg-rust-900/30
                border border-rust-800/40 px-2 py-1 rounded-lg">
                {gaps.length} gap{gaps.length !== 1 ? "s" : ""}
              </span>
            )}
          </div>

          {gaps.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-xs text-teal-600">
                No gaps logged yet — questions with strong matches in
                the materials won&apos;t appear here.
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {gaps.map((gap) => (
                <div
                  key={gap.id}
                  className="flex items-start justify-between gap-4
                    p-3 rounded-lg bg-rust-900/20 border border-rust-800/20"
                >
                  <p className="text-xs text-teal-200 leading-relaxed flex-1">
                    {gap.query}
                  </p>
                  <div className="flex flex-col items-end gap-1 flex-shrink-0">
                    <span className="text-[10px] text-rust-400 bg-rust-900/40
                      border border-rust-800/50 px-1.5 py-0.5 rounded">
                      {(gap.confidence * 100).toFixed(0)}% match
                    </span>
                    <span className="text-[10px] text-teal-700">
                      {formatDate(gap.asked_at)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Footer ──────────────────────────────────────────────────── */}
        <div className="mt-8 flex items-center justify-between">
          <p className="text-[11px] text-teal-700">
            Curra AI Prototype · DAV · Strathmore University MSc IT 2026
          </p>
          <Link
            href="/"
            className="text-[11px] text-teal-600 hover:text-teal-400
              transition-colors"
          >
            Back to home
          </Link>
        </div>

      </div>
    </div>
  );
}