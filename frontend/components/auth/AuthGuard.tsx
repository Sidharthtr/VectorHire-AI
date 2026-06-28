"use client";
/**
 * Client-side route guard — only renders children when a user is signed in.
 *
 * What it does:
 * - Reads { user, ready } from AuthContext; while ready=false shows "Loading…"
 * - If ready and no user, redirects to /login via router.replace
 * - Otherwise renders children unchanged
 *
 * Upstream (who imports this OR which URL renders it): app/(app)/layout.tsx (wraps every protected page)
 * Downstream (what this imports): next/navigation useRouter, @/contexts/AuthContext
 */
// useEffect — runs the redirect-to-login side effect after auth state resolves
import { useEffect } from "react";
// useRouter — router.replace("/login") so users can't go "back" to a protected page
import { useRouter } from "next/navigation";
// useAuth — source of truth for the current user and the `ready` hydration flag
import { useAuth } from "@/contexts/AuthContext";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, ready } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (ready && !user) {
      router.replace("/login");
    }
  }, [ready, user, router]);

  if (!ready || !user) {
    return (
      <div className="flex items-center justify-center min-h-[50vh] text-gray-500 text-sm">
        Loading…
      </div>
    );
  }

  return <>{children}</>;
}
