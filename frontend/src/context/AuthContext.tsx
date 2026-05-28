"use client";

/**
 * context/AuthContext.tsx
 * ========================
 * Authentication state provider.
 *
 * LIFECYCLE:
 *   1. Mount → check localStorage for token
 *   2. Token exists → GET /auth/me → hydrate user
 *   3. Token invalid → clear silently, user=null
 *   4. login()  → POST /auth/login → store token → GET /auth/me → set user
 *   5. signup() → POST /auth/signup → auto-login → set user
 *   6. logout() → remove token → user=null
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";

import * as authService from "@/services/auth";
import { getStoredToken } from "@/services/api";
import { ApiError } from "@/services/api";
import type {
  AuthContextValue,
  LoginPayload,
  SignupPayload,
  UserResponse,
} from "@/types/auth";

// ─── Context ──────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

// ─── Provider ─────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Restore session on mount
  useEffect(() => {
    let cancelled = false;

    async function restore() {
      const token = getStoredToken();
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const me = await authService.getMe();
        if (!cancelled) setUser(me);
      } catch {
        authService.logout();
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    restore();
    return () => { cancelled = true; };
  }, []);

  // Actions
  const login = useCallback(async (payload: LoginPayload): Promise<UserResponse> => {
    setError(null);
    try {
      await authService.login(payload);
      const me = await authService.getMe();
      setUser(me);
      return me;
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : "Login failed";
      setError(msg);
      throw err;
    }
  }, []);

  const signup = useCallback(async (payload: SignupPayload): Promise<UserResponse> => {
    setError(null);
    try {
      await authService.signup(payload);
      await authService.login({ email: payload.email, password: payload.password });
      const me = await authService.getMe();
      setUser(me);
      return me;
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : "Signup failed";
      setError(msg);
      throw err;
    }
  }, []);

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
    setError(null);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return (
    <AuthContext.Provider
      value={{ user, loading, error, login, signup, logout, clearError }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ─── Context Consumer (for internal use + useAuth hook) ───────────────

export function useAuthContext(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}