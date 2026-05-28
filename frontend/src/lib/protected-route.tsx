"use client";

/**
 * lib/protected-route.ts
 * =======================
 * Route guards — ProtectedRoute and GuestGuard.
 *
 * ProtectedRoute: redirects unauthenticated users to /login
 * GuestGuard:     redirects authenticated users to /
 *
 * WHY COMPONENTS, NOT MIDDLEWARE?
 *   Next.js middleware runs on the edge — no React Context access.
 *   It can check for a cookie, but can't validate the JWT session.
 *   Component guards know the REAL auth state via useAuth().
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

// ─── Spinner ──────────────────────────────────────────────────────────

function Spinner() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#09090B]">
      <Loader2 className="h-5 w-5 animate-spin text-zinc-400" />
    </div>
  );
}

// ─── ProtectedRoute ───────────────────────────────────────────────────

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) return <Spinner />;
  return <>{children}</>;
}

// ─── GuestGuard ───────────────────────────────────────────────────────

export function GuestGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.replace("/");
  }, [loading, user, router]);

  if (loading || user) return <Spinner />;
  return <>{children}</>;
}
