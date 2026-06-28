/**
 * Shared TypeScript types mirroring backend Pydantic schemas.
 *
 * What it does:
 * - Declares the request/response shapes used by lib/api.ts and every UI component
 * - Keeps a single source of truth so backend/frontend stay in sync
 *
 * Upstream (who imports this): lib/api.ts, contexts/AuthContext.tsx, HistoryContext.tsx,
 *   hooks/useAnalysis.ts, hooks/useJobSearch.ts, components/results/*, components/jobs/*,
 *   components/chat/ChatPanel.tsx, app/(app)/analysis/[id]/page.tsx
 * Downstream (what this imports): none — pure type declarations
 */

// Resume parsing types — sub-structures returned by the resume parser
export interface Education {
  institution: string;
  degree: string;
  field?: string;
  graduation_year?: string;
  gpa?: string;
}

export interface WorkExperience {
  company: string;
  role: string;
  duration: string;
  description: string;
  skills_used: string[];
}

export interface Project {
  name: string;
  description: string;
  technologies: string[];
  url?: string;
}

export interface ParsedResume {
  raw_text: string;
  name?: string;
  email?: string;
  phone?: string;
  location?: string;
  summary?: string;
  skills: string[];
  education: Education[];
  experience: WorkExperience[];
  projects: Project[];
  certifications: string[];
  years_of_experience?: number;
  experience_level?: string;
}

// Job types — job postings and ranked match results
export interface JobDocument {
  id: string;
  title: string;
  company: string;
  location: string;
  experience_level: string;
  employment_type: string;
  skills: string[];
  description: string;
  responsibilities: string[];
  requirements: string[];
  salary_range?: string;
  remote: boolean;
}

export interface RankedJob {
  job: JobDocument;
  similarity_score: number;
  match_percentage: number;
  matched_skills: string[];
  missing_skills: string[];
  explanation?: string;
}

// Analysis types — payloads from /resume/analyze and /analysis/history
export interface AnalysisResponse {
  success: boolean;
  resume_id: string;
  analysis_id?: string;
  top_jobs: RankedJob[];
  overall_match_summary: string;
  top_missing_skills: string[];
  improvement_suggestions: string[];
  processing_time_ms?: number;
}

export interface AnalysisSummary {
  id: string;
  resume_name: string;
  top_match_pct: number | null;
  job_count: number;
  created_at: string;
}

// Auth types — current user and JWT response
export interface User {
  id: string;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

// Search types — standalone job search payload
export interface JobSearchResponse {
  success: boolean;
  query: string;
  total_results: number;
  jobs: RankedJob[];
  processing_time_ms?: number;
}

// Resume upload type — payload from /resume/upload
export interface ResumeUploadResponse {
  success: boolean;
  message: string;
  resume_id: string;
  parsed_resume?: ParsedResume;
}

// System types — backend /health probe response
export interface HealthResponse {
  status: string;
  version: string;
  services: Record<string, boolean>;
}

// Chat types — streaming chat roles and persisted messages
export type ChatRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  created_at: string;
}
