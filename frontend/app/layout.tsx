/* 
  layout.tsx — root layout component.
  
  In Next.js App Router, layout.tsx is a special file that wraps all pages
  within the same directory. This root layout wraps every page in the app.
  
  It sets the HTML document structure (the parts that go in <head>),
  applies global styles, and provides a consistent shell for all pages.
*/

import type { Metadata } from "next";
import "./globals.css";

// Metadata is exported from layout files and Next.js uses it to populate
// the <head> of the HTML document — browser tab title, SEO description, etc.
export const metadata: Metadata = {
  title: "Curra AI",
  description: "Curriculum-grounded study assistant for Data Analytics and Visualisation",
};

export default function RootLayout({
  children,
}: {
  // children represents whatever page is currently being rendered.
  // The layout renders around it — like a picture frame around the content.
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      {/* 
        antialiased: smooths font rendering at the CSS level.
        min-h-screen: ensures the page fills the full viewport height
        even when content is short.
        bg-gray-950: near-black background for the dark study interface.
        text-white: default text colour applied to all children.
      */}
      <body className="antialiased min-h-screen bg-gray-950 text-white">
        {children}
      </body>
    </html>
  );
}