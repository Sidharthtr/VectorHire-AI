"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import AnalysisResults from "@/components/results/AnalysisResults";
import ChatPanel from "@/components/chat/ChatPanel";
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
