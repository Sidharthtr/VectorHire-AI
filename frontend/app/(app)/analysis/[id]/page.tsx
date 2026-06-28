"use client";
/**
 * Detail view for a saved analysis — reopen past results plus chat about them.
 *
 * What it does:
 * - Reads :id from the dynamic route and fetches the analysis from the backend
 * - Renders the same AnalysisResults panel used on /upload, but for stored data
 * - Mounts ChatPanel so the user can ask the Career Coach follow-up questions
 *
 * Upstream (who imports this OR which URL renders it): Next.js — URL: /analysis/[id] (linked from Sidebar history)
 * Downstream (what this imports): @/lib/api, AnalysisResults, ChatPanel, AnalysisResponse type
 */
// useEffect — fetch when :id changes; useState — store result/error/loading flags
import { useEffect, useState } from "react";
// useParams — read the [id] dynamic segment from the URL on the client
import { useParams } from "next/navigation";
// api — wraps GET /analyses/:id (used here as api.getAnalysis)
import { api } from "@/lib/api";
// AnalysisResults — reuse the same results UI as /upload to render the saved analysis
import AnalysisResults from "@/components/results/AnalysisResults";
// ChatPanel — streaming Q&A about THIS analysis, scoped via analysisId prop
import ChatPanel from "@/components/chat/ChatPanel";
// AnalysisResponse type — shape of the fetched analysis (top_jobs, summary, suggestions, etc.)
import type { AnalysisResponse } from "@/types";

export default function AnalysisDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;

  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    api.getAnalysis(id)
      .then(setResult)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Failed to load analysis"),
      )
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[40vh] text-gray-500 text-sm">
        Loading analysis…
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto bg-red-50 border border-red-200 text-red-700 rounded-xl p-6">
        <h2 className="font-bold mb-1">Could not load analysis</h2>
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  if (!result) return null;

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Saved Analysis</h1>
        <p className="text-gray-600 mt-1">
          Review your matches, skill gaps, and improvement roadmap.
        </p>
      </div>
      <AnalysisResults result={result} />
      <ChatPanel analysisId={result.analysis_id ?? (id as string)} />
    </div>
  );
}
