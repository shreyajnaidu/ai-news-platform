/**
 * summarizer.ts — AI Summary Service
 * ====================================
 * Calls the backend summarization endpoint.
 *
 * ENDPOINT: POST /articles/{id}/summary
 * Response: { summary: string[], sentiment: string, reading_time: string }
 *
 * The backend runs NLP to generate bullet-point summaries and
 * sentiment analysis. This service just fetches and types the result.
 */

import axios, { type AxiosError, type AxiosInstance } from "axios";

// ─── Configuration ────────────────────────────────────────────────────

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15_000, // longer timeout — NLP takes time
  headers: {
    "Content-Type": "application/json",
  },
});

// ─── Types ────────────────────────────────────────────────────────────

export interface SummaryResult {
  /** Bullet-point summaries of the article */
  summary: string[];
  /** Sentiment label: "positive", "negative", "neutral" */
  sentiment: string;
  /** Estimated reading time, e.g. "3 min read" */
  reading_time: string;
}

export interface SummaryError {
  message: string;
}

// ─── Error Handling ───────────────────────────────────────────────────

export class SummaryApiError extends Error {
  public readonly status: number | null;
  public readonly detail: string;

  constructor(status: number | null, detail: string) {
    super(detail);
    this.name = "SummaryApiError";
    this.status = status;
    this.detail = detail;
  }
}

// ─── API Function ─────────────────────────────────────────────────────

/**
 * Get AI-generated summary for a specific article.
 *
 * @param articleId — the article's database ID
 * @returns SummaryResult with bullets, sentiment, and reading time
 *
 * @throws SummaryApiError on network failure, 404, 500, etc.
 */
export async function summarizeArticle(
  article: any,
): Promise<SummaryResult> {
  try {
    const response = await api.post<SummaryResult>(
  "articles/summarize",
  {
    title: article.title,
    content: article.description || article.title || article.title,
    source: article.source,
  }
);

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosErr = error as AxiosError<{ detail?: string }>;

      const status = axiosErr.response?.status ?? null;

      const serverMessage = axiosErr.response?.data?.detail;

      const networkMessage = axiosErr.message;

      const detail =
        status === 500
    ? "AI summary service is temporarily busy. Please try again shortly."
    : serverMessage ??
      (status
        ? `Server error (${status})`
        : `Network error: ${networkMessage}`);

      throw new SummaryApiError(status, detail);
      
    }

    throw new SummaryApiError(
      null,
      "Failed to generate summary",
    );
  }
}
