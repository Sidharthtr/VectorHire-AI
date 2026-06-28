/**
 * Tiny localStorage wrapper for the JWT auth token.
 *
 * What it does:
 * - Reads/writes/clears the "vh_token" key in window.localStorage
 * - Guards against SSR by checking `typeof window` before touching browser APIs
 *
 * Upstream (who imports this): lib/api.ts (attaches token to requests),
 *   contexts/AuthContext.tsx (sets on login, clears on logout)
 * Downstream (what this imports): none — pure browser storage helpers
 */
const TOKEN_KEY = "vh_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
}
