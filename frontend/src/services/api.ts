/**
 * api.ts — Service Layer
 * ======================
 * The single bridge between Next.js frontend and FastAPI backend.
 *
 * IMPORTANT: This file uses ONLY standard Tailwind classes and
 * inline styles with hex/rgba values — no custom theme utilities
 * that might not be configured.
 */

import axios, { type AxiosError, type AxiosInstance } from "axios";

// ─── Configuration ────────────────────────────────────────────────────

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

// ─── Axios Instance ───────────────────────────────────────────────────

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10_000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ─── Error Handling ───────────────────────────────────────────────────

export class ApiError extends Error {
  public readonly status: number | null;
  public readonly detail: string;

  constructor(status: number | null, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function handleApiError(error: unknown): never {
  if (axios.isAxiosError(error)) {
    const axiosErr = error as AxiosError<{ detail?: string }>;
    const status = axiosErr.response?.status ?? null;
    const serverMessage = axiosErr.response?.data?.detail;
    const networkMessage = axiosErr.message;

    const detail =
      serverMessage ??
      (status
        ? `Server error (${status})`
        : `Network error: ${networkMessage}`);

    throw new ApiError(status, detail);
  }

  throw new ApiError(null, "An unexpected error occurred");
}

// ─── Shared Types ─────────────────────────────────────────────────────
// FeedArticle matches what GET /feed returns per the user's spec:
// { id, title, description, category, source, url, image_url,
//   published_at, score }

export interface FeedArticle {
  id: number;
  title: string;
  description: string | null;
  category: string | null;
  source: string | null;
  url: string;
  image_url: string | null;
  published_at: string | null;
  score: number;
}

export interface FeedResponse {
  count: number;
  feed: FeedArticle[];
}

// ─── API Functions ────────────────────────────────────────────────────

/**
 * Fetch the personalized, ranked news feed.
 * Calls GET /feed on the FastAPI backend.
 */
export async function fetchFeed(): Promise<FeedResponse> {
  try {
    const response = await api.get<FeedResponse>("/feed");
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
}