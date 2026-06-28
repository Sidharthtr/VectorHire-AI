"use client";
/**
 * Hook that performs a standalone job search (no resume required).
 *
 * What it does:
 * - Holds the latest query, results, loading flag, and error message
 * - Calls api.searchJobs with optional topK and experience level filters
 * - Surfaces backend errors as a string so the UI can render them
 *
 * Upstream (who imports this): app/(app)/dashboard/page.tsx (job search UI)
 * Downstream (what this imports): react useState, @/lib/api, @/types
 */
// useState — local state for query, results, loading, and error
import { useState } from "react";
// api — calls POST /search/jobs
import { api } from "@/lib/api";
// RankedJob — shape of each job result returned with similarity score
import type { RankedJob } from "@/types";

export function useJobSearch() {
  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState<RankedJob[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  const search = async (searchQuery: string, topK = 10, experienceLevel?: string) => {
    setLoading(true);
    setError(null);
    setQuery(searchQuery);

    try {
      const data = await api.searchJobs(searchQuery, topK, experienceLevel);
      setJobs(data.jobs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  };

  return { loading, jobs, query, error, search };
}
