"use client";
import { useState } from "react";
import { Search, Filter } from "lucide-react";
import { useJobSearch } from "@/hooks/useJobSearch";
import JobList from "@/components/jobs/JobList";

const SAMPLE_QUERIES = [
  "AI backend intern FastAPI LangGraph",
  "Remote RAG engineering entry level",
  "LLMOps engineer Docker Kubernetes",
  "Agentic AI developer LangGraph multi-agent",
  "Vector search engineer ChromaDB Pinecone",
  "ML infrastructure engineer PyTorch AWS",
];

const EXPERIENCE_LEVELS = [
  { value: "", label: "All levels" },
  { value: "intern", label: "Internship" },
  { value: "entry", label: "Entry level" },
  { value: "mid", label: "Mid level" },
  { value: "senior", label: "Senior" },
];

export default function DashboardPage() {
  const [query, setQuery] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("");
  const [topK, setTopK] = useState(10);
  const { loading, jobs, error, search } = useJobSearch();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      search(query.trim(), topK, experienceLevel || undefined);
    }
  };

  const handleSampleQuery = (q: string) => {
    setQuery(q);
    search(q, topK, experienceLevel || undefined);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Job Search</h1>
        <p className="text-gray-600 mt-1">Semantically search our AI/backend job database using natural language.</p>
      </div>

      {/* Search Form */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Remote RAG engineering roles with LangChain..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div className="flex gap-3">
            <div className="flex items-center gap-2">
              <Filter size={15} className="text-gray-400" />
              <select
                value={experienceLevel}
                onChange={(e) => setExperienceLevel(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                {EXPERIENCE_LEVELS.map((l) => (
                  <option key={l.value} value={l.value}>{l.label}</option>
                ))}
              </select>
            </div>

            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
              <option value={20}>Top 20</option>
            </select>

            <button
              type="submit"
              disabled={!query.trim() || loading}
              className="bg-brand-600 hover:bg-brand-700 disabled:bg-gray-300 text-white px-6 py-2 rounded-lg font-semibold text-sm transition-colors"
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>
        </form>

        {/* Sample queries */}
        <div>
          <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">Try a sample query:</p>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => handleSampleQuery(q)}
                className="text-xs bg-gray-100 hover:bg-brand-50 hover:text-brand-700 text-gray-600 px-3 py-1.5 rounded-full transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-600">
          {error}
        </div>
      )}

      {loading && (
        <div className="text-center py-12 text-gray-500">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-brand-600 border-t-transparent mx-auto mb-3" />
          Searching...
        </div>
      )}

      {!loading && jobs.length > 0 && (
        <div>
          <p className="text-sm text-gray-500 mb-4">
            Found <strong>{jobs.length}</strong> matching jobs
          </p>
          <JobList jobs={jobs} />
        </div>
      )}

      {!loading && jobs.length === 0 && !error && (
        <div className="text-center py-12 text-gray-400">
          <Search size={40} className="mx-auto mb-3 opacity-30" />
          <p>Enter a search query above to find matching jobs.</p>
        </div>
      )}
    </div>
  );
}
