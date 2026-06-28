"use client";
/**
 * Provides the sidebar's list of past resume analyses for the logged-in user.
 *
 * What it does:
 * - Fetches /analysis/history whenever the auth user changes
 * - Tracks loading/error state and exposes a `refresh()` so pages can re-fetch after an analysis
 * - Empties the list when there is no signed-in user
 *
 * Upstream (who imports this): app/(app)/layout.tsx (mounts HistoryProvider),
 *   app/(app)/upload/page.tsx (calls refresh after analysis), components/layout/Sidebar.tsx
 * Downstream (what this imports): react, @/lib/api, ./AuthContext, @/types
 */
// React context + hooks used to build the provider and memoise the refresh callback
import { createContext, useCallback, useContext, useEffect, useState } from "react";
// api — calls GET /analysis/history to populate the sidebar
import { api } from "@/lib/api";
// useAuth — only fetch history when a user is signed in; clear it on logout
import { useAuth } from "./AuthContext";
// AnalysisSummary — row shape rendered by the sidebar history list
import type { AnalysisSummary } from "@/types";

type HistoryState = {
  items: AnalysisSummary[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
};

const HistoryContext = createContext<HistoryState | null>(null);

export function HistoryProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [items, setItems] = useState<AnalysisSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!user) {
      setItems([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.getHistory();
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load history");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <HistoryContext.Provider value={{ items, loading, error, refresh }}>
      {children}
    </HistoryContext.Provider>
  );
}

export function useHistory(): HistoryState {
  const ctx = useContext(HistoryContext);
  if (!ctx) throw new Error("useHistory must be used inside <HistoryProvider>");
  return ctx;
}
