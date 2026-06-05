"use client";
import { useState } from "react";
import { api } from "@/lib/api";
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
