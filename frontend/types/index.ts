// ============================================================
// Shared TypeScript types matching backend Pydantic schemas
// ============================================================

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

export interface User {
  id: string;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface JobSearchResponse {
  success: boolean;
  query: string;
  total_results: number;
  jobs: RankedJob[];
  processing_time_ms?: number;
}

export interface ResumeUploadResponse {
  success: boolean;
  message: string;
  resume_id: string;
  parsed_resume?: ParsedResume;
}

export interface HealthResponse {
  status: string;
  version: string;
  services: Record<string, boolean>;
}

export type ChatRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  created_at: string;
}
