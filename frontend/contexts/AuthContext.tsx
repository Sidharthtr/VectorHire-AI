"use client";
/**
 * Client-side authentication provider and `useAuth` hook.
 *
 * What it does:
 * - Hydrates the current user on mount by calling /auth/me with the stored JWT
 * - Exposes login/register/logout actions that persist the token and refresh the user
 * - Throws if `useAuth` is used outside the provider so misuse is caught early
 *
 * Upstream (who imports this): app/layout.tsx (mounts AuthProvider),
 *   app/login/page.tsx, app/register/page.tsx, app/page.tsx,
 *   components/auth/AuthGuard.tsx, components/layout/Sidebar.tsx, HistoryContext.tsx
 * Downstream (what this imports): react, next/navigation, @/lib/api, @/lib/auth-storage, @/types
 */
// createContext/useContext/useState/useEffect/useCallback — React primitives powering this provider's state machine
import { createContext, useCallback, useContext, useEffect, useState } from "react";
// useRouter — to redirect to /login after logout
import { useRouter } from "next/navigation";
// api — wraps backend HTTP calls used here (login, register, getMe)
import { api } from "@/lib/api";
// token helpers — persist the JWT across reloads and clear it on logout
import { clearToken, getToken, setToken } from "@/lib/auth-storage";
// User — shape of the authenticated user returned by /auth/me
import type { User } from "@/types";

type AuthState = {
  user: User | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setReady(true);
      return;
    }
    api.getMe()
      .then(setUser)
      .catch(() => {
        clearToken();
        setUser(null);
      })
      .finally(() => setReady(true));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await api.login(email, password);
    setToken(access_token);
    const me = await api.getMe();
    setUser(me);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const { access_token } = await api.register(email, password);
    setToken(access_token);
    const me = await api.getMe();
    setUser(me);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, ready, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
