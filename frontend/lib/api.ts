const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => request<{ status: string; version: string; services: Record<string, boolean> }>("/health"),

  uploadResume: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<import("@/types").ResumeUploadResponse>("/resume/upload", {
      method: "POST",
      body: form,
    });
  },

  analyzeResume: (file: File, searchQuery?: string, topK = 10) => {
    const form = new FormData();
    form.append("file", file);
    const params = new URLSearchParams({ top_k: String(topK) });
    if (searchQuery) params.append("search_query", searchQuery);
    return request<import("@/types").AnalysisResponse>(`/resume/analyze?${params}`, {
      method: "POST",
      body: form,
    });
  },

  searchJobs: (query: string, topK = 10, experienceLevel?: string) => {
    return request<import("@/types").JobSearchResponse>("/search/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: topK, experience_level: experienceLevel }),
    });
  },
};
