/*
  page.tsx — home page, served at the root URL (/).
  
  In Next.js App Router, every file named page.tsx inside the app/
  directory becomes a routable URL. This one lives at app/page.tsx
  so it maps to http://localhost:3000/.

  At this prototype stage, the home page is a simple landing screen
  with two call-to-action buttons. It will be redesigned in Phase 5
  once the backend is functional and we know exactly what to surface here.
*/

import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      
      {/* 
        Header block — product name and unit scope.
        The subtitle makes it immediately clear this is scoped
        to one course, which sets the right expectation for the lecturer demo.
      */}
      <div className="text-center mb-10">
        <h1 className="text-5xl font-bold tracking-tight mb-3">
          Curra AI
        </h1>
        <p className="text-gray-400 text-lg">
          Data Analytics and Visualisation — Study Assistant
        </p>
        <p className="text-gray-600 text-sm mt-2">
          Answers from your actual course materials. Not the internet.
        </p>
      </div>

      {/* 
        Navigation buttons.
        Link from next/link is used instead of <a> tags because it
        handles client-side navigation without a full page reload.
      */}
      <div className="flex gap-4">
        <Link
          href="/modes"
          className="px-6 py-3 bg-indigo-600 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          Choose a Study Mode
        </Link>
        <Link
          href="/chat"
          className="px-6 py-3 bg-gray-800 rounded-lg text-sm font-medium hover:bg-gray-700 transition-colors"
        >
          Free Chat
        </Link>
      </div>

    </main>
  );
}