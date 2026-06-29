/*
  page.tsx — Curra AI home page at /.

  Minimal landing screen that communicates the product's core value
  proposition before routing the student into a study mode.
  No navigation chrome — just the name, tagline, and two entry points.
*/

import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center
      p-8 bg-teal-950">

      {/* Subtle background texture */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))]
        from-teal-900/20 via-transparent to-transparent pointer-events-none" />

      <div className="relative text-center max-w-lg">
        {/* Logo mark */}
        <div className="inline-flex items-center justify-center w-12 h-12
          rounded-2xl bg-teal-800 border border-teal-700 mb-6">
          <svg className="w-6 h-6 text-teal-400" fill="none"
            stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168
              5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477
              4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0
              3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5
              18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        </div>

        <h1 className="text-4xl font-medium tracking-tight text-teal-100 mb-3">
          Curra AI
        </h1>
        <p className="text-teal-300 text-lg mb-2">
          Data Analytics and Visualisation
        </p>
        <p className="text-teal-500 text-sm mb-10">
          Answers from your actual lecture slides. Not the internet.
        </p>

        {/* Entry points */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/modes"
            className="px-6 py-3 bg-teal-600 hover:bg-teal-500 text-teal-50
              rounded-xl text-sm font-medium transition-colors"
          >
            Choose a study mode
          </Link>
          <Link
            href="/chat"
            className="px-6 py-3 bg-teal-800/60 hover:bg-teal-800
              text-teal-200 border border-teal-700 rounded-xl text-sm
              font-medium transition-colors"
          >
            Free chat
          </Link>
        </div>

        {/* Unit scope indicator */}
        <p className="mt-10 text-[11px] text-teal-700">
          Strathmore University · MSc IT · Semester 1 2026
        </p>
      </div>
    </main>
  );
}