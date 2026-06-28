/**
 * Two-column skill comparison — "You Have" vs "You Need" for a single job.
 *
 * What it does:
 * - Renders matched skills as green chips and missing skills as red chips
 * - Shows counts in each section header for quick scanning
 * - Falls back to a gray placeholder when either array is empty
 *
 * Upstream (who imports this OR which URL renders it): components/jobs/JobCard.tsx (inside the expanded panel)
 * Downstream (what this imports): lucide-react icons only (purely presentational)
 */
// CheckCircle2 / XCircle — green check next to "You Have", red X next to "You Need"
import { CheckCircle2, XCircle } from "lucide-react";

interface SkillGapProps {
  matched: string[];
  missing: string[];
}

export default function SkillGap({ matched, missing }: SkillGapProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div>
        <h4 className="text-sm font-semibold text-green-700 mb-2 flex items-center gap-1">
          <CheckCircle2 size={14} />
          You Have ({matched.length})
        </h4>
        <div className="flex flex-wrap gap-1.5">
          {matched.length > 0 ? (
            matched.map((skill) => (
              <span key={skill} className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-md font-medium">
                {skill}
              </span>
            ))
          ) : (
            <span className="text-xs text-gray-400">No matching skills identified</span>
          )}
        </div>
      </div>

      <div>
        <h4 className="text-sm font-semibold text-red-600 mb-2 flex items-center gap-1">
          <XCircle size={14} />
          You Need ({missing.length})
        </h4>
        <div className="flex flex-wrap gap-1.5">
          {missing.length > 0 ? (
            missing.map((skill) => (
              <span key={skill} className="text-xs bg-red-100 text-red-600 px-2 py-1 rounded-md font-medium">
                {skill}
              </span>
            ))
          ) : (
            <span className="text-xs text-gray-400">No skill gaps identified</span>
          )}
        </div>
      </div>
    </div>
  );
}
