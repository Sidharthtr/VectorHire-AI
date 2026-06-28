/**
 * Thin list wrapper — renders a JobCard per RankedJob, or an empty state.
 *
 * What it does:
 * - Accepts a jobs[] array and an optional emptyMessage override
 * - Renders a centered placeholder when the array is empty
 * - Otherwise spaces JobCards vertically and passes a 1-based rank to each
 *
 * Upstream (who imports this OR which URL renders it): components/results/AnalysisResults.tsx, app/(app)/dashboard/page.tsx
 * Downstream (what this imports): @/types RankedJob, ./JobCard
 */
// RankedJob — type for each item in the jobs[] prop (the LLM-ranked match shape)
import type { RankedJob } from "@/types";
// JobCard — one rendered row per RankedJob; this component is purely a layout wrapper
import JobCard from "./JobCard";

interface JobListProps {
  jobs: RankedJob[];
  emptyMessage?: string;
}

export default function JobList({ jobs, emptyMessage = "No jobs found." }: JobListProps) {
  if (jobs.length === 0) {
    return (
      <div className="text-center py-16 text-gray-500">
        <p className="text-lg">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {jobs.map((rankedJob, index) => (
        <JobCard key={rankedJob.job.id} rankedJob={rankedJob} rank={index + 1} />
      ))}
    </div>
  );
}
