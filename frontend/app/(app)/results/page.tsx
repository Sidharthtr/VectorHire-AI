"use client";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function ResultsPage() {
  return (
    <div className="max-w-2xl mx-auto text-center py-16 space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Analysis Results</h1>
      <p className="text-gray-600">
        Results are displayed directly on the{" "}
        <Link href="/upload" className="text-brand-600 hover:underline font-medium">
          Upload & Analyze
        </Link>{" "}
        page after running the pipeline.
      </p>
      <Link
        href="/upload"
        className="inline-flex items-center gap-2 text-brand-600 hover:text-brand-700 font-medium"
      >
        <ArrowLeft size={16} />
        Go to Resume Analyzer
      </Link>
    </div>
  );
}
