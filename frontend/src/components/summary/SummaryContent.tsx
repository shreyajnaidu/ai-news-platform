"use client";

/**
 * SummaryContent.tsx
 * ==================
 * Renders the loaded AI summary — bullets, sentiment, reading time.
 *
 * LAYOUT:
 *   ┌─────────────────────────────┐
 *   │  Reading time    Sentiment  │  ← metadata row
 *   │─────────────────────────────│
 *   │  • First summary bullet     │
 *   │  • Second summary bullet    │
 *   │  • Third summary bullet     │
 *   │─────────────────────────────│
 *   │  Source: Reuters            │  ← source attribution
 *   │  [  Read Full Article   ]   │  ← CTA button
 *   └─────────────────────────────┘
 */

import type { SummaryResult } from "@/services/summarizer";
import { SentimentBadge } from "./SentimentBadge";

interface SummaryContentProps {
  data: SummaryResult;
  articleUrl: string;
  articleSource: string | null;
}

export function SummaryContent({
  data,
  articleUrl,
  articleSource,
}: SummaryContentProps) {
  return (
    <div className="space-y-6">
      {/* ── Metadata row ──────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3">
        <span className="inline-flex items-center gap-1.5 text-xs text-zinc-400">
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            className="text-zinc-500"
          >
            <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1" />
            <path d="M6 3V6L8 7.5" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
          </svg>
          {data.reading_time}
        </span>

        <SentimentBadge sentiment={data.sentiment} />
      </div>

      {/* ── Divider ───────────────────────────────────────────────── */}
      <div
        className="h-px w-full"
        style={{ backgroundColor: "rgba(255,255,255,0.06)" }}
      />

      {/* ── Summary bullets ───────────────────────────────────────── */}
      <div className="space-y-3">
        <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
          AI Summary
        </p>
        <ul className="space-y-2.5">
          {data.summary.map((bullet, i) => (
            <li key={i} className="flex items-start gap-3">
              <span
                className="mt-[7px] h-1 w-1 shrink-0 rounded-full"
                style={{ backgroundColor: "#8B5CF6" }}
              />
              <span className="text-sm leading-relaxed text-zinc-300">
                {bullet}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* ── Divider ───────────────────────────────────────────────── */}
      <div
        className="h-px w-full"
        style={{ backgroundColor: "rgba(255,255,255,0.06)" }}
      />

      {/* ── Source + CTA ──────────────────────────────────────────── */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {articleSource && (
          <span className="text-xs text-zinc-500">
            Source:{" "}
            <span className="text-zinc-400">{articleSource}</span>
          </span>
        )}

        <a
          href={articleUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="group inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-medium text-white transition-all duration-200"
          style={{ backgroundColor: "#8B5CF6" }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "#A78BFA";
            e.currentTarget.style.boxShadow =
              "0 4px 16px rgba(139,92,246,0.2)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "#8B5CF6";
            e.currentTarget.style.boxShadow = "none";
          }}
        >
          Read Full Article
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            className="transition-transform group-hover:translate-x-0.5"
          >
            <path
              d="M1 6H11M11 6L6 1M11 6L6 11"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </a>
      </div>
    </div>
  );
}
