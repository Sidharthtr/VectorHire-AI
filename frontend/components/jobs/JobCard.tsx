"use client";
/**
 * Single job result card — shows the job header, match % and an expandable detail panel.
 *
 * What it does:
 * - Renders title/company/location, remote pill, experience pill, and salary range
 * - Highlights skills the user already has (green) vs. the rest (gray)
 * - Expands to show the LLM explanation, SkillGap component, and full description
 *
 * Upstream (who imports this OR which URL renders it): @/components/jobs/JobList
 * Downstream (what this imports): @/lib/utils formatters, @/types RankedJob, ./SkillGap
 */
// useState — local "expanded" toggle for the details section
import { useState } from "react";
// lucide-react icons — location/company pills, expand chevrons, and Wifi for "Remote"
import { MapPin, Building2, ChevronDown, ChevronUp, Wifi } from "lucide-react";
// utils — cn (class merge), formatMatchPercentage (display %), getMatchColor (red/yellow/green), capitalize
import { cn, formatMatchPercentage, getMatchColor, capitalize } from "@/lib/utils";
// RankedJob — the job + match metadata shape produced by the LangGraph ranker
import type { RankedJob } from "@/types";
// SkillGap — renders matched-vs-missing skill chips inside the expanded detail panel
import SkillGap from "./SkillGap";

interface JobCardProps {
  rankedJob: RankedJob;
  rank: number;
}

export default function JobCard({ rankedJob, rank }: JobCardProps) {
  const [expanded, setExpanded] = useState(false);
  const { job, match_percentage, matched_skills, missing_skills, explanation } = rankedJob;

  const matchColor = getMatchColor(match_percentage);
  const matchBg =
    match_percentage >= 75 ? "bg-green-50 border-green-200" :
    match_percentage >= 50 ? "bg-yellow-50 border-yellow-200" :
    "bg-red-50 border-red-200";

  return (
    <div className="bg-white rounded-xl border border-gray-200 hover:shadow-md transition-shadow overflow-hidden">
      {/* Header */}
      <div className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold text-gray-400 uppercase">#{rank}</span>
              <span className="text-xs bg-brand-50 text-brand-600 px-2 py-0.5 rounded-full font-medium">
                {capitalize(job.experience_level)}
              </span>
              {job.remote && (
                <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full font-medium flex items-center gap-1">
                  <Wifi size={10} />
                  Remote
                </span>
              )}
            </div>
            <h3 className="font-bold text-gray-900 text-lg truncate">{job.title}</h3>
            <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <Building2 size={13} />
                {job.company}
              </span>
              <span className="flex items-center gap-1">
                <MapPin size={13} />
                {job.location}
              </span>
            </div>
            {job.salary_range && (
              <p className="text-sm text-gray-600 mt-1 font-medium">{job.salary_range}</p>
            )}
          </div>

          {/* Match Score */}
          <div className={cn("text-center rounded-xl border p-3 shrink-0 min-w-[80px]", matchBg)}>
            <p className={cn("text-2xl font-bold", matchColor)}>
              {formatMatchPercentage(match_percentage)}
            </p>
            <p className="text-xs text-gray-500 font-medium">match</p>
          </div>
        </div>

        {/* Skills preview */}
        <div className="flex flex-wrap gap-1.5 mt-4">
          {job.skills.slice(0, 6).map((skill) => {
            const isMatched = matched_skills.some(s => s.toLowerCase() === skill.toLowerCase());
            return (
              <span
                key={skill}
                className={cn(
                  "text-xs px-2 py-1 rounded-md font-medium",
                  isMatched ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"
                )}
              >
                {skill}
              </span>
            );
          })}
          {job.skills.length > 6 && (
            <span className="text-xs px-2 py-1 rounded-md bg-gray-100 text-gray-500">
              +{job.skills.length - 6} more
            </span>
          )}
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-sm text-brand-600 hover:text-brand-700 font-medium mt-4 transition-colors"
        >
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          {expanded ? "Show less" : "View details & skill gap"}
        </button>
      </div>

      {/* Expanded */}
      {expanded && (
        <div className="border-t border-gray-100 p-6 space-y-5 bg-gray-50">
          {explanation && (
            <div>
              <h4 className="text-sm font-semibold text-gray-800 mb-2">AI Match Explanation</h4>
              <p className="text-sm text-gray-700 leading-relaxed bg-white rounded-lg p-4 border border-gray-200">
                {explanation}
              </p>
            </div>
          )}

          <SkillGap matched={matched_skills} missing={missing_skills} />

          <div>
            <h4 className="text-sm font-semibold text-gray-800 mb-2">About This Role</h4>
            <p className="text-sm text-gray-600 leading-relaxed line-clamp-4">{job.description}</p>
          </div>
        </div>
      )}
    </div>
  );
}
