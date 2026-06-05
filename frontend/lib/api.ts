import { getToken } from "./auth-storage";
import type {
  AnalysisResponse,
  AnalysisSummary,
  AuthResponse,
  ChatMessage,
  HealthResponse,
  JobSearchResponse,
  ResumeUploadResponse,
  User,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => request<HealthResponse>("/health"),

  register: (email: string, password: string) =>
    request<AuthResponse>("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    }),

  getMe: () => request<User>("/auth/me"),

  uploadResume: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<ResumeUploadResponse>("/resume/upload", {
      method: "POST",
      body: form,
    });
  },

  analyzeResume: (file: File, searchQuery?: string, topK = 10) => {
    const form = new FormData();
    form.append("file", file);
    const params = new URLSearchParams({ top_k: String(topK) });
    if (searchQuery) params.append("search_query", searchQuery);
    return request<AnalysisResponse>(`/resume/analyze?${params}`, {
      method: "POST",
      body: form,
    });
  },

  searchJobs: (query: string, topK = 10, experienceLevel?: string) => {
    return request<JobSearchResponse>("/search/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: topK, experience_level: experienceLevel }),
    });
  },

  getHistory: () => request<AnalysisSummary[]>("/analysis/history"),

  getAnalysis: (id: string) => request<AnalysisResponse>(`/analysis/${id}`),

  getMessages: (id: string) => request<ChatMessage[]>(`/analysis/${id}/messages`),

  /**
   * Stream a chat reply token-by-token. Returns the full final reply string.
   * `onToken` is called for each incoming chunk so the UI can render incrementally.
   * `signal` lets the caller abort the request.
   */
  streamChat: async (
    id: string,
    content: string,
    onToken: (chunk: string) => void,
    signal?: AbortSignal,
  ): Promise<string> => {
    const token = getToken();
    const res = await fetch(`${API_BASE}/analysis/${id}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ content }),
      signal,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const reader = res.body?.getReader();
    if (!reader) throw new Error("Streaming not supported");
    const decoder = new TextDecoder();
    let full = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      full += chunk;
      onToken(chunk);
    }
    full += decoder.decode();
    return full;
  },
};
