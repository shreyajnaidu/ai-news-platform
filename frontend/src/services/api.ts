/**
 * services/api.ts
 * ================
 * Centralized HTTP client + token storage + XTransformPort gateway routing.
 *
 * LAYERS:
 *   1. Token helpers — SSR-safe localStorage read/write/remove
 *   2. ApiError      — typed error with status + detail
 *   3. api instance  — fetch wrapper that auto-injects JWT, handles 401
 *
 * WHY NOT AXIOS?
 *   Zero dependencies. Native fetch. Interceptors are just code.
 */

import type { ApiErrorResponse } from "@/types/auth";

// ─── Token Storage ────────────────────────────────────────────────────

const TOKEN_KEY = "auth_access_token";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeStoredToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

// ─── Gateway Port Routing ─────────────────────────────────────────────


// ─── Custom Error ─────────────────────────────────────────────────────

export class ApiError extends Error {
  public status: number;
  public detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

// ─── Request Core ─────────────────────────────────────────────────────

type Method = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  params?: Record<string, string | string[]>;
  noAuth?: boolean;
}

function buildUrl(path: string, params?: Record<string, string | string[]>): string {
  const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const url = new URL(path, API_BASE_URL);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      (Array.isArray(value) ? value : [value]).forEach((v) =>
        url.searchParams.append(key, v),
      );
    });
  }
  return url.toString();
}

async function request<T>(
  method: Method,
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, params, noAuth = false, headers: extraHeaders, ...rest } = options;

  const headers = new Headers(extraHeaders);
  headers.set("Content-Type", "application/json");

  if (!noAuth) {
    const token = getStoredToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const url = buildUrl(path, params);

  const response = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(15_000),
    ...rest,
  });

  if (!response.ok) {
    if (response.status === 401) removeStoredToken();

    let detail = `Request failed (${response.status})`;
    try {
      const errBody: ApiErrorResponse = await response.json();
      if (errBody.detail) detail = errBody.detail;
    } catch { /* not JSON */ }

    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

// ─── Public API ───────────────────────────────────────────────────────

export const api = {
  get: <T>(path: string, opts?: RequestOptions) =>
    request<T>("GET", path, opts),

  post: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>("POST", path, { ...opts, body }),

  put: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>("PUT", path, { ...opts, body }),

  delete: <T>(path: string, opts?: RequestOptions) =>
    request<T>("DELETE", path, opts),
};

// ─── Wake / Health Ping ────────────────────────────────────────────────
// Render free tier spins down the backend after inactivity.
// This pings /health up to 10 times (30s total) to wake it up,
// so the first feed fetch doesn't get a connection error.

export class WakeTimeoutError extends Error {
  constructor() {
    super("Backend server did not wake up in time");
    this.name = "WakeTimeoutError";
  }
}

const WAKE_RETRIES = 10;
const WAKE_INTERVAL_MS = 3000;

export async function wakeBackend(): Promise<void> {
  const baseUrl =
    process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

  for (let attempt = 1; attempt <= WAKE_RETRIES; attempt++) {
    try {
      const resp = await fetch(`${baseUrl}/health`, {
        signal: AbortSignal.timeout(5_000),
      });
      if (resp.ok) return;
    } catch {
      // Server is still sleeping — will throw on cold Render instance
    }

    if (attempt < WAKE_RETRIES) {
      console.log(`Waking backend... (attempt ${attempt}/${WAKE_RETRIES})`);
      await new Promise((r) => setTimeout(r, WAKE_INTERVAL_MS));
    }
  }

  throw new WakeTimeoutError();
}

// ─── Feed Types ──────────────────────────────────────────────────────

export interface FeedArticle {
  id: number;
  title: string;
  description: string | null;
  category: string | null;
  source: string | null;
  url: string;
  image_url: string | null;
  published_at: string | null;

  ml_score?: number;
  personalization_boost?: number;
  importance_boost?: number;
  freshness_boost?: number;
  quality_score?: number;
  final_score?: number;
}

export interface FeedResponse {
  count: number;
  feed: FeedArticle[];
}

// ─── Feed API ────────────────────────────────────────────────────────

export async function fetchFeed(): Promise<FeedResponse> {
  return api.get<FeedResponse>("/feed");
}
