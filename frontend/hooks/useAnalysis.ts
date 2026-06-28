"use client";
/**
 * Hook that runs a resume analysis and tracks its lifecycle status.
 *
 * What it does:
 * - Drives the status state machine: idle → uploading → analyzing → done/error
 * - Calls api.analyzeResume with the chosen file and optional search query
 * - Fires an optional onSuccess callback (used to refresh the sidebar history)
 *
 * Upstream (who imports this): app/(app)/upload/page.tsx (the analyze UI)
 * Downstream (what this imports): react useState, @/lib/api, @/types
 */
// useState — local state for status / result / error
import { useState } from "react";
// api — calls POST /resume/analyze
import { api } from "@/lib/api";
// AnalysisResponse — shape of the analyze endpoint's payload
import type { AnalysisResponse } from "@/types";

type Status = "idle" | "uploading" | "analyzing" | "done" | "error";

export function useAnalysis(onSuccess?: () => void | Promise<void>) {
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const analyze = async (file: File, searchQuery?: string) => {
    setStatus("uploading");
    setError(null);
    setResult(null);

    try {
      setStatus("analyzing");
      const data = await api.analyzeResume(file, searchQuery);
      setResult(data);
      setStatus("done");
      if (onSuccess) await onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
      setStatus("error");
    }
  };

  const reset = () => {
    setStatus("idle");
    setResult(null);
    setError(null);
  };

  return { status, result, error, analyze, reset };
}
