"use client";
/**
 * Renders a full AnalysisResponse — summary cards, AI summary, gaps, suggestions, jobs.
 *
 * What it does:
 * - Shows three summary tiles (matched-job count, best match %, skills-to-learn count)
 * - Renders the LLM career summary, top missing skills, and a numbered improvement roadmap
 * - Delegates the ranked-jobs list to JobList
 *
 * Upstream (who imports this OR which URL renders it): app/(app)/upload/page.tsx, app/(app)/analysis/[id]/page.tsx
 * Downstream (what this imports): @/components/jobs/JobList, lucide-react icons, @/types AnalysisResponse
 */
// JobList — handles rendering the ranked job array via JobCards
import JobList from "@/components/jobs/JobList";
// lucide-react icons — Zap/TrendingUp/Target tile icons + Lightbulb for the AI summary header
import { Lightbulb, Target, TrendingUp, Zap } from "lucide-react";
// AnalysisResponse — typed shape of the pipeline output (top_jobs, summary, suggestions, missing skills)
import type { AnalysisResponse } from "@/types";

export default function AnalysisResults({ result }: { result: AnalysisResponse }) {
  return (
    <div className="space-y-8">
      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <Zap size={24} className="mx-auto text-brand-600 mb-2" />
          <p className="text-2xl font-bold text-gray-900">{result.top_jobs.length}</p>
          <p className="text-sm text-gray-500">Matched Jobs</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <TrendingUp size={24} className="mx-auto text-green-500 mb-2" />
          <p className="text-2xl font-bold text-gray-900">
            {result.top_jobs[0]
              ? `${Math.round(result.top_jobs[0].match_percentage)}%`
              : "—"}
          </p>
          <p className="text-sm text-gray-500">Best Match</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <Target size={24} className="mx-auto text-orange-500 mb-2" />
          <p className="text-2xl font-bold text-gray-900">{result.top_missing_skills.length}</p>
          <p className="text-sm text-gray-500">Skills to Learn</p>
        </div>
      </div>

      {/* AI Summary */}
      {result.overall_match_summary && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
            <Lightbulb size={18} className="text-brand-600" />
            AI Career Summary
          </h2>
          <p className="text-gray-700 leading-relaxed">{result.overall_match_summary}</p>
        </div>
      )}

      {/* Missing Skills */}
      {result.top_missing_skills.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-bold text-gray-900 mb-3">Top Skills to Learn</h2>
          <div className="flex flex-wrap gap-2">
            {result.top_missing_skills.map((skill) => (
              <span
                key={skill}
                className="bg-orange-100 text-orange-700 text-sm px-3 py-1 rounded-full font-medium"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Suggestions */}
      {result.improvement_suggestions.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-bold text-gray-900 mb-3">Improvement Roadmap</h2>
          <ol className="space-y-2">
            {result.improvement_suggestions.map((suggestion, i) => (
              <li key={i} className="flex gap-3 text-sm text-gray-700">
                <span className="w-6 h-6 rounded-full bg-brand-600 text-white text-xs flex items-center justify-center shrink-0 font-bold">
                  {i + 1}
                </span>
                {suggestion}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Job Matches */}
      <div>
        <h2 className="font-bold text-gray-900 text-xl mb-4">Your Job Matches</h2>
        <JobList
          jobs={result.top_jobs}
          emptyMessage="No jobs found. Make sure the vector DB is seeded."
        />
      </div>
    </div>
  );
}
