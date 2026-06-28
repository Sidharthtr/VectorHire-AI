"use client";
/**
 * "New Analysis" page — drives the resume → AI pipeline → results flow.
 *
 * What it does:
 * - Holds the chosen File and optional search-focus text in local state
 * - Delegates the upload + LangGraph pipeline call to the useAnalysis hook
 * - Swaps the UI between idle/uploading/analyzing/error/done states
 *
 * Upstream (who imports this OR which URL renders it): Next.js — URL: /upload (default landing for signed-in users)
 * Downstream (what this imports): upload + results components, useAnalysis hook, useHistory context
 */
// useState — tracks the selected File and the optional free-text "search focus" query
import { useState } from "react";
// ResumeUpload — drag-and-drop PDF picker that calls onFileSelect when a file is chosen
import ResumeUpload from "@/components/upload/ResumeUpload";
// UploadProgress — visual stepper showing uploading → analyzing → done/error
import UploadProgress from "@/components/upload/UploadProgress";
// AnalysisResults — summary cards + job matches + skill roadmap shown after the pipeline finishes
import AnalysisResults from "@/components/results/AnalysisResults";
// useAnalysis — owns the POST /analyze call, status state machine, and parsed result
import { useAnalysis } from "@/hooks/useAnalysis";
// useHistory — gives us refresh() so the Sidebar list re-fetches after a new analysis is saved
import { useHistory } from "@/contexts/HistoryContext";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const { refresh } = useHistory();
  const { status, result, error, analyze, reset } = useAnalysis(refresh);

  const handleSubmit = async () => {
    if (!file) return;
    await analyze(file, searchQuery || undefined);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Analyze Your Resume</h1>
        <p className="text-gray-600 mt-1">
          Upload your PDF resume to get personalized job matches and skill gap analysis.
        </p>
      </div>

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

      {status === "done" && result && (
        <div className="space-y-8">
          <UploadProgress status={status} />
          <AnalysisResults result={result} />
          <button
            onClick={reset}
            className="text-sm text-gray-500 hover:text-brand-600 transition-colors"
          >
            ← Analyze another resume
          </button>
        </div>
      )}
    </div>
  );
}
