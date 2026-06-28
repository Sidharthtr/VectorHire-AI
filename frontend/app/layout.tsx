/**
 * Root layout for the Next.js App Router — wraps every route in the app.
 *
 * What it does:
 * - Sets <html>/<body>, applies Inter font and base Tailwind background
 * - Exports Next.js metadata (title/description) used by the document head
 * - Wraps the tree with AuthProvider so any page can read the current user
 *
 * Upstream (who imports this OR which URL renders it): Next.js — renders for ALL routes (/, /login, /register, /(app)/*)
 * Downstream (what this imports): next/font Inter, ./globals.css (Tailwind), @/contexts/AuthContext
 */
// Metadata type — gives the exported `metadata` object proper typing for Next.js head tags
import type { Metadata } from "next";
// Inter font loader — Next.js self-hosts the font; we apply its className on <body>
import { Inter } from "next/font/google";
// Global Tailwind/base styles — must be imported once at the root
import "./globals.css";
// AuthProvider — exposes the user/login/logout context to every descendant page and component
import { AuthProvider } from "@/contexts/AuthContext";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "VectorHire AI — Career Copilot",
  description:
    "Agentic AI-powered career copilot. Upload your resume, find matching jobs, and understand your skill gaps.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} min-h-screen bg-gray-50`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
