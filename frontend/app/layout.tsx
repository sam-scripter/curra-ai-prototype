import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Curra AI — DAV Study Assistant",
  description:
    "Curriculum-grounded AI study assistant for Data Analytics and Visualisation at Strathmore University",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      {/*
        min-h-screen: ensures every page fills the full viewport.
        antialiased: smooth font rendering.
        Colors come from globals.css CSS variables.
      */}
      <body className="antialiased min-h-screen bg-teal-950 text-teal-100">
        {children}
      </body>
    </html>
  );
}