"use client";

/**
 * SummaryModal.tsx
 * ================
 * Premium 3D cinematic modal for AI article summarization.
 *
 * STRUCTURE:
 *   1. AnimatePresence wrapper (for enter/exit animations)
 *   2. Blurred backdrop (click to close)
 *   3. Modal panel with glass-lg effect
 *      - Close button
 *      - Article header (title, image, source, time)
 *      - Summary content OR skeleton OR error
 *
 * 3D EFFECTS:
 *   - Modal scales from 0.96 → 1.0 on open
 *   - Subtle perspective on the content wrapper
 *   - Backdrop fades in with blur
 *   - Exit reverses the enter animation
 */

import { motion, AnimatePresence } from "framer-motion";
import type { FeedArticle } from "@/services/api";
import type { SummaryResult } from "@/services/summarizer";
import { modalBackdrop, modalContent } from "@/lib/animations";
import { SummaryContent } from "./SummaryContent";
import { SummarySkeleton } from "./SummarySkeleton";

interface SummaryModalProps {
  isOpen: boolean;
  article: FeedArticle | null;
  summary: SummaryResult | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}

/** Format ISO date into a relative time string */
function formatTime(iso: string | null): string | null {
  if (!iso) return null;
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  const diffHr = Math.floor(diffMs / 3_600_000);
  const diffDay = Math.floor(diffMs / 86_400_000);

  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function SummaryModal({
  isOpen,
  article,
  summary,
  loading,
  error,
  onClose,
}: SummaryModalProps) {
  // Prevent body scroll when modal is open
  if (typeof document !== "undefined" && isOpen) {
    document.body.style.overflow = "hidden";
  } else if (typeof document !== "undefined") {
    document.body.style.overflow = "";
  }

  return (
    <AnimatePresence>
      {isOpen && article && (
        <>
          {/* ── Backdrop ──────────────────────────────────────────── */}
          <motion.div
            className="fixed inset-0 z-40"
            style={{
              backgroundColor: "rgba(0, 0, 0, 0.6)",
              backdropFilter: "blur(8px)",
              WebkitBackdropFilter: "blur(8px)",
            }}
            variants={modalBackdrop}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={onClose}
          />

          {/* ── Modal panel ───────────────────────────────────────── */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
            <motion.div
              className="relative w-full max-w-lg overflow-hidden rounded-2xl"
              style={{
                backgroundColor: "rgba(30, 30, 35, 0.92)",
                border: "1px solid rgba(255, 255, 255, 0.10)",
                backdropFilter: "blur(24px)",
                WebkitBackdropFilter: "blur(24px)",
                boxShadow:
                  "0 8px 32px rgba(0,0,0,0.3), 0 0 0 1px rgba(139,92,246,0.05)",
              }}
              variants={modalContent}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={(e) => e.stopPropagation()}
            >
              {/* ── Surface gradient ─────────────────────────────── */}
              <div
                className="pointer-events-none absolute inset-0 z-0"
                style={{
                  background:
                    "linear-gradient(180deg, rgba(255,255,255,0.02) 0%, transparent 30%)",
                }}
              />

              {/* ── Close button ──────────────────────────────────── */}
              <button
                onClick={onClose}
                className="absolute right-4 top-4 z-20 flex h-8 w-8 items-center justify-center rounded-lg text-zinc-500 transition-colors duration-150 hover:bg-white/[0.06] hover:text-zinc-300"
                aria-label="Close"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 14 14"
                  fill="none"
                >
                  <path
                    d="M1 1L13 13M13 1L1 13"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  />
                </svg>
              </button>

              {/* ── Content ──────────────────────────────────────── */}
              <div className="relative z-10 max-h-[80vh] overflow-y-auto p-6 sm:p-8">
                {/* Article image */}
                {article.image_url && (
                  <div
                    className="mb-5 overflow-hidden rounded-xl"
                    style={{
                      aspectRatio: "16/9",
                      backgroundColor: "#111114",
                    }}
                  >
                    <img
                      src={article.image_url}
                      alt=""
                      className="h-full w-full object-cover"
                      loading="lazy"
                    />
                  </div>
                )}

                {/* Category */}
                {article.category && (
                  <span
                    className="mb-3 inline-block rounded-full px-2.5 py-0.5 text-[11px] font-medium"
                    style={{
                      backgroundColor: "rgba(139, 92, 246, 0.08)",
                      color: "#A78BFA",
                    }}
                  >
                    {article.category}
                  </span>
                )}

                {/* Title */}
                <h2
                  className="mb-2 text-lg font-semibold leading-snug tracking-[-0.01em]"
                  style={{ color: "#FAFAFA" }}
                >
                  {article.title}
                </h2>

                {/* Source + time */}
                <div className="mb-6 flex items-center gap-2 text-[11px] text-zinc-500">
                  {article.source && (
                    <>
                      <span className="font-medium text-zinc-400">
                        {article.source}
                      </span>
                      <span className="text-zinc-600">·</span>
                    </>
                  )}
                  {article.published_at && (
                    <span>{formatTime(article.published_at)}</span>
                  )}
                </div>

                {/* Summary area — loading / loaded / error */}
               {/* ── Summary area ───────────────────────────────────── */}
{error ? (
  <div
    className="rounded-2xl p-5"
    style={{
      backgroundColor: "rgba(255,255,255,0.03)",
      border: "1px solid rgba(255,255,255,0.06)",
    }}
  >
    <p className="text-sm leading-relaxed text-zinc-300">
      AI summary service is temporarily busy. Please try again shortly.
    </p>

    {article.url && (
      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-4 inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-all duration-200 hover:scale-[1.02]"
        style={{
          backgroundColor: "rgba(139, 92, 246, 0.10)",
          color: "#C4B5FD",
          border: "1px solid rgba(139, 92, 246, 0.18)",
        }}
      >
        View Full Article →
      </a>
    )}
  </div>
) : loading ? (
  <SummarySkeleton />
) : summary ? (
  <>
    <SummaryContent
      data={summary}
      articleUrl={article.url}
      articleSource={article.source}
    />

    {article.url && (
      <div className="mt-6">
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-all duration-200 hover:scale-[1.02]"
          style={{
            backgroundColor: "rgba(139, 92, 246, 0.10)",
            color: "#C4B5FD",
            border: "1px solid rgba(139, 92, 246, 0.18)",
          }}
        >
          View Full Article →
        </a>
      </div>
    )}
  </>
) : null}
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
