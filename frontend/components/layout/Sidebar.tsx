"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brain, FileText, History, LogOut, Plus, Search } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useHistory } from "@/contexts/HistoryContext";

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { items, loading } = useHistory();

  const navLink = (href: string, label: string, Icon: typeof Plus) => {
    const active = pathname === href;
    return (
      <Link
        href={href}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
          active
            ? "bg-brand-50 text-brand-700"
            : "text-gray-700 hover:bg-gray-100"
        }`}
      >
        <Icon size={16} />
        {label}
      </Link>
    );
  };

  return (
    <aside className="w-72 shrink-0 bg-white border-r border-gray-200 flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <Link
        href="/upload"
        className="flex items-center gap-2 px-5 py-4 border-b border-gray-200"
      >
        <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
          <Brain size={18} className="text-white" />
        </div>
        <span className="font-bold text-gray-900">VectorHire AI</span>
      </Link>

      {/* Main nav */}
      <nav className="px-3 py-3 space-y-1 border-b border-gray-200">
        {navLink("/upload", "New Analysis", Plus)}
        {navLink("/dashboard", "Job Search", Search)}
      </nav>

      {/* History */}
      <div className="flex-1 overflow-y-auto px-3 py-3">
        <div className="flex items-center gap-2 px-2 py-1 text-xs font-semibold text-gray-500 uppercase tracking-wide">
          <History size={12} />
          History
        </div>

        {loading && items.length === 0 ? (
          <p className="px-2 py-3 text-xs text-gray-400">Loading…</p>
        ) : items.length === 0 ? (
          <p className="px-2 py-3 text-xs text-gray-400">
            No analyses yet. Upload a resume to start.
          </p>
        ) : (
          <ul className="space-y-1 mt-1">
            {items.map((item) => {
              const href = `/analysis/${item.id}`;
              const active = pathname === href;
              return (
                <li key={item.id}>
                  <Link
                    href={href}
                    className={`block px-2 py-2 rounded-lg text-sm transition-colors ${
                      active
                        ? "bg-brand-50 text-brand-700"
                        : "text-gray-700 hover:bg-gray-100"
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <FileText size={14} className="mt-0.5 shrink-0 text-gray-400" />
                      <div className="flex-1 min-w-0">
                        <p className="truncate font-medium">{item.resume_name}</p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {item.top_match_pct != null
                            ? `${Math.round(item.top_match_pct)}% match · `
                            : ""}
                          {item.job_count} job{item.job_count === 1 ? "" : "s"}
                          {" · "}
                          {formatDate(item.created_at)}
                        </p>
                      </div>
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* User footer */}
      <div className="px-3 py-3 border-t border-gray-200">
        <div className="flex items-center justify-between px-2">
          <div className="min-w-0">
            <p className="text-xs text-gray-500">Signed in as</p>
            <p className="text-sm font-medium text-gray-900 truncate">
              {user?.email}
            </p>
          </div>
          <button
            onClick={logout}
            title="Sign out"
            className="p-2 text-gray-500 hover:text-brand-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}
