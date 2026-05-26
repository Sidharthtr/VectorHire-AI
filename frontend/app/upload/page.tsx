"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import ResumeUpload from "@/components/upload/ResumeUpload";
import UploadProgress from "@/components/upload/UploadProgress";
import JobList from "@/components/jobs/JobList";
import { useAnalysis } from "@/hooks/useAnalysis";
import { Lightbulb, Target, TrendingUp, Zap } from "lucide-react";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const { status, result, error, analyze, reset } = useAnalysis();

  const handleSubmit = async () => {
    if (!file) return;
    await analyze(file, searchQuery || undefined);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Analyze Your Resume</h1>
        <p className="text-gray-600 mt-1">Upload your PDF resume to get personalized job matches and skill gap analysis.</p>
      </div>

      {/* Upload form */}
      {status === "idle" && (
        <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-5">
          <ResumeUpload onFileSelect={setFile} />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search focus <span className="text-gray-400">(optional)</span>
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="e.g. remote RAG engineering roles, AI backend internships..."
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={!file}
            className="w-full bg-brand-600 hover:bg-brand-700 disabled:bg-gray-300 text-white py-3 rounded-lg font-semibold transition-colors"
          >
            Analyze with AI
          </button>
        </div>
      )}

      {/* Progress */}
      {(status === "uploading" || status === "analyzing") && (
        <div className="space-y-4">
          <UploadProgress status={status} error={error} />
          <div className="bg-brand-50 rounded-xl p-4 border border-brand-100">
            <p className="text-sm text-brand-700 font-medium">
              The AI is running your resume through 5 processing steps: parse → extract → retrieve → rank → explain.
              This may take 30–60 seconds on first run.
            </p>
          </div>
        </div>
      )}

      {status === "error" && (
        <div className="space-y-3">
          <UploadProgress status={status} error={error} />
          <button onClick={reset} className="text-sm text-brand-600 hover:underline">
            ← Try again
          </button>
        </div>
      )}

      {/* Results */}
      {status === "done" && result && (
        <div className="space-y-8">
          <UploadProgress status={status} />

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
                {result.top_jobs[0] ? `${Math.round(result.top_jobs[0].match_percentage)}%` : "—"}
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
                  <span key={skill} className="bg-orange-100 text-orange-700 text-sm px-3 py-1 rounded-full font-medium">
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

          <button onClick={reset} className="text-sm text-gray-500 hover:text-brand-600 transition-colors">
            ← Analyze another resume
          </button>
        </div>
      )}
    </div>
  );
}
