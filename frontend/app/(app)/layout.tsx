/**
 * Protected layout for the (app) route group — wraps every authenticated page.
 *
 * What it does:
 * - Gates the subtree behind AuthGuard so unauthenticated users get bounced to /login
 * - Supplies HistoryProvider so the sidebar/pages can read past analyses
 * - Renders the persistent Sidebar next to a centered <main> content area
 *
 * Upstream (who imports this OR which URL renders it): Next.js — wraps every (app)/* page: /upload, /dashboard, /analysis/[id]
 * Downstream (what this imports): @/components/auth/AuthGuard, @/components/layout/Sidebar, @/contexts/HistoryContext
 */
// AuthGuard — client component that redirects to /login if the user isn't authenticated
import AuthGuard from "@/components/auth/AuthGuard";
// Sidebar — persistent left rail with navigation links and analysis history list
import Sidebar from "@/components/layout/Sidebar";
// HistoryProvider — fetches and caches the user's prior analyses for the Sidebar + pages
import { HistoryProvider } from "@/contexts/HistoryContext";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <HistoryProvider>
        <div className="flex min-h-screen bg-gray-50">
          <Sidebar />
          <main className="flex-1 overflow-x-hidden">
            <div className="max-w-5xl mx-auto px-6 py-8">{children}</div>
          </main>
        </div>
      </HistoryProvider>
    </AuthGuard>
  );
}
