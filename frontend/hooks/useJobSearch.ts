"use client";
import { useState } from "react";
import { api } from "@/lib/api";
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
