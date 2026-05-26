import type { RankedJob } from "@/types";
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
