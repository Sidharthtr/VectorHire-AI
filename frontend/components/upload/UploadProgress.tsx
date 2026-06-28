"use client";
/**
 * Stepper UI — visualizes the upload/analysis status received from useAnalysis.
 *
 * What it does:
 * - Hides itself when status is "idle"; otherwise shows a 3-step checklist
 * - Picks the right icon per step (spinning, checked, or unchecked outline)
 * - Renders a red error message when status === "error"
 *
 * Upstream (who imports this OR which URL renders it): app/(app)/upload/page.tsx
 * Downstream (what this imports): lucide-react icons only (pure presentational)
 */
// lucide-react icons — Loader2 for in-progress spin, CheckCircle2 for done, XCircle for error
import { Loader2, CheckCircle2, XCircle } from "lucide-react";

type Status = "idle" | "uploading" | "analyzing" | "done" | "error";

const steps = [
  { key: "uploading", label: "Uploading resume" },
  { key: "analyzing", label: "Running AI analysis pipeline" },
  { key: "done", label: "Analysis complete" },
];

interface UploadProgressProps {
  status: Status;
  error?: string | null;
}

export default function UploadProgress({ status, error }: UploadProgressProps) {
  if (status === "idle") return null;

  const currentStepIndex = steps.findIndex((s) => s.key === status);
  const isError = status === "error";

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
      <h3 className="font-semibold text-gray-900">Analysis Progress</h3>

      {isError ? (
        <div className="flex items-center gap-3 text-red-600">
          <XCircle size={20} />
          <span className="text-sm">{error || "Analysis failed. Please try again."}</span>
        </div>
      ) : (
        <div className="space-y-3">
          {steps.map((step, i) => {
            const isDone = status === "done" || i < currentStepIndex;
            const isCurrent = step.key === status;

            return (
              <div key={step.key} className="flex items-center gap-3">
                {isDone ? (
                  <CheckCircle2 size={18} className="text-green-500 shrink-0" />
                ) : isCurrent ? (
                  <Loader2 size={18} className="text-brand-600 animate-spin shrink-0" />
                ) : (
                  <div className="w-[18px] h-[18px] rounded-full border-2 border-gray-300 shrink-0" />
                )}
                <span className={`text-sm ${isCurrent ? "text-brand-600 font-medium" : isDone ? "text-gray-700" : "text-gray-400"}`}>
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {status === "done" && (
        <p className="text-sm text-green-600 font-medium">
          ✓ Scroll down to see your results
        </p>
      )}
    </div>
  );
}
