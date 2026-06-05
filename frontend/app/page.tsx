"use client";
import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Brain, Search, TrendingUp, Zap } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

const features = [
  {
    icon: Brain,
    title: "AI Resume Analysis",
    description:
      "Upload your PDF resume and get instant AI-powered skill extraction and profile building.",
  },
  {
    icon: Search,
    title: "Semantic Job Search",
    description:
      "Goes beyond keyword matching — find jobs that truly fit your experience using vector embeddings.",
  },
  {
    icon: TrendingUp,
    title: "Skill Gap Analysis",
    description:
      "Understand exactly which skills you're missing for your target roles and what to learn next.",
  },
  {
    icon: Zap,
    title: "Personalized Explanations",
    description:
      "Get clear, actionable explanations of why each job is or isn't the right fit for you.",
  },
];

export default function HomePage() {
  const router = useRouter();
  const { user, ready } = useAuth();

  useEffect(() => {
    if (ready && user) router.replace("/upload");
  }, [ready, user, router]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
      {/* Top bar */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
            <Brain size={18} className="text-white" />
          </div>
          <span className="font-bold text-gray-900 text-lg">VectorHire AI</span>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="text-sm font-medium text-gray-700 hover:text-brand-600"
          >
            Sign in
          </Link>
          <Link
            href="/register"
            className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Get started
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="text-center py-8 space-y-6">
        <div className="inline-flex items-center gap-2 bg-brand-50 text-brand-600 px-4 py-2 rounded-full text-sm font-medium border border-brand-100">
          <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse" />
          Powered by LangGraph + OpenRouter
        </div>
        <h1 className="text-5xl font-bold tracking-tight text-gray-900">
          Your AI-Powered <span className="gradient-text">Career Copilot</span>
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Upload your resume, discover perfectly matched AI jobs, and get a clear
          roadmap to land your dream role.
        </p>
        <div className="flex justify-center gap-4">
          <Link
            href="/register"
            className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            Analyze My Resume
            <ArrowRight size={18} />
          </Link>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 bg-white hover:bg-gray-50 text-gray-700 px-6 py-3 rounded-lg font-semibold border border-gray-200 transition-colors"
          >
            Sign in
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {features.map((feature) => (
          <div
            key={feature.title}
            className="bg-white rounded-xl p-6 border border-gray-200 hover:border-brand-300 hover:shadow-md transition-all"
          >
            <div className="w-10 h-10 bg-brand-50 rounded-lg flex items-center justify-center mb-4">
              <feature.icon size={20} className="text-brand-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
            <p className="text-sm text-gray-600 leading-relaxed">{feature.description}</p>
          </div>
        ))}
      </section>

      {/* How it works */}
      <section className="bg-white rounded-2xl border border-gray-200 p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-center">
          {[
            { step: "1", label: "Upload Resume" },
            { step: "→", label: "" },
            { step: "2", label: "AI Parses Skills" },
            { step: "→", label: "" },
            { step: "3", label: "Semantic Matching" },
          ].map((item, i) => (
            <div key={i} className="text-center">
              {item.step === "→" ? (
                <div className="text-gray-300 text-2xl hidden md:block">→</div>
              ) : (
                <div className="space-y-2">
                  <div className="w-12 h-12 bg-brand-600 text-white rounded-full flex items-center justify-center font-bold text-lg mx-auto">
                    {item.step}
                  </div>
                  <p className="text-sm font-medium text-gray-700">{item.label}</p>
                </div>
              )}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-center mt-4">
          {[
            { step: "4", label: "LLM Ranking" },
            { step: "→", label: "" },
            { step: "5", label: "Explanations" },
            { step: "→", label: "" },
            { step: "6", label: "Skill Roadmap" },
          ].map((item, i) => (
            <div key={i} className="text-center">
              {item.step === "→" ? (
                <div className="text-gray-300 text-2xl hidden md:block">→</div>
              ) : (
                <div className="space-y-2">
                  <div className="w-12 h-12 bg-brand-600 text-white rounded-full flex items-center justify-center font-bold text-lg mx-auto">
                    {item.step}
                  </div>
                  <p className="text-sm font-medium text-gray-700">{item.label}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
