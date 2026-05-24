"use client";

/**
 * FeedSection.tsx
 * ===============
 * Fetches the AI-ranked feed, renders a responsive card grid,
 * and manages the summary modal lifecycle.
 *
 * RESPONSIBILITIES:
 *   1. Call fetchFeed() on mount
 *   2. Show loading skeleton while waiting
 *   3. Show error state if the API fails
 *   4. Render articles in a responsive grid with stagger animation
 *   5. Manage selected article + summary modal state via useSummary hook
 *
 * Uses ONLY standard Tailwind classes + inline styles with hex/rgba.
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fetchFeed, ApiError, type FeedArticle } from "@/services/api";
import { useSummary } from "@/hooks/useSummary";
import { NewsCard } from "./NewsCard";
import { SummaryModal } from "@/components/summary/SummaryModal";
import { staggerGrid, blurIn, ease } from "@/lib/animations";

// ─── Types ────────────────────────────────────────────────────────────

interface FeedData {
  count: number;
  feed: FeedArticle[];
}

// ─── Animation ────────────────────────────────────────────────────────

const cardEntrance = {
  hidden: { opacity: 0, y: 16, filter: "blur(4px)" },
  visible: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { duration: 0.45, ease: ease.out },
  },
};

// ─── Loading Skeleton ─────────────────────────────────────────────────

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="animate-pulse overflow-hidden rounded-xl p-0"
          style={{
            backgroundColor: "#18181B",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          {/* Image placeholder */}
          <div className="h-40 w-full" style={{ backgroundColor: "#111114" }} />
          <div className="space-y-3 p-5">
            <div className="h-4 w-20 rounded-full" style={{ backgroundColor: "#111114" }} />
            <div className="h-5 w-3/4 rounded" style={{ backgroundColor: "#111114" }} />
            <div className="h-4 w-full rounded" style={{ backgroundColor: "#111114" }} />
            <div className="h-4 w-2/3 rounded" style={{ backgroundColor: "#111114" }} />
            <div className="h-3 w-24 rounded" style={{ backgroundColor: "#111114" }} />
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Error State ──────────────────────────────────────────────────────

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div
        className="mb-4 flex h-12 w-12 items-center justify-center rounded-full"
        style={{ backgroundColor: "rgba(248,113,113,0.1)" }}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
          style={{ color: "#F87171" }}
        >
          <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.5" />
          <path d="M10 6V11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <circle cx="10" cy="14" r="1" fill="currentColor" />
        </svg>
      </div>
      <p className="mb-1 text-sm font-medium text-zinc-100">
        Unable to load feed
      </p>
      <p className="mb-5 text-xs text-zinc-500">{message}</p>
      <button
        onClick={onRetry}
        className="rounded-lg px-4 py-2 text-xs font-medium text-zinc-400 transition-colors duration-200 hover:text-zinc-200"
        style={{ border: "1px solid rgba(255,255,255,0.08)" }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = "rgba(255,255,255,0.15)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)";
        }}
      >
        Try again
      </button>
    </div>
  );
}

// ─── FeedSection ──────────────────────────────────────────────────────

export function FeedSection() {
  const [data, setData] = useState<FeedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const {
    selectedArticle,
    isOpen,
    summary,
    loading: summaryLoading,
    error: summaryError,
    openSummary,
    closeSummary,
  } = useSummary();

  function loadFeed() {
    setLoading(true);
    setError(null);

    fetchFeed()
      .then((response) => {
        setData(response);
      })
      .catch((err) => {
        if (err instanceof ApiError) {
          setError(err.detail);
        } else {
          setError("Something went wrong. Please try again.");
        }
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadFeed();
  }, []);

  return (
    <section className="relative px-6 py-20 md:px-10 lg:py-28">
      {/* ── Section heading ──────────────────────────────────────── */}
      <motion.div
        className="mb-12 max-w-2xl"
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.5, ease: ease.out }}
      >
        <span
          className="mb-3 block text-[11px] font-medium uppercase tracking-wider"
          style={{ color: "#A78BFA" }}
        >
          Your Intelligence Feed
        </span>
        <h2 className="text-2xl font-semibold tracking-[-0.02em] text-zinc-50 md:text-3xl">
          Stories ranked for you
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-zinc-400 md:text-base">
          Every article scored by relevance, sentiment, and impact — so you see
          what matters first.
        </p>
      </motion.div>

      {/* ── Content ──────────────────────────────────────────────── */}
      {error ? (
        <ErrorState message={error} onRetry={loadFeed} />
      ) : loading ? (
        <SkeletonGrid />
      ) : data && data.feed.length > 0 ? (
        <motion.div
          className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3"
          variants={staggerGrid}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-60px" }}
        >
          {data.feed.map((article) => (
            <motion.div key={article.id} variants={cardEntrance}>
              <NewsCard article={article} onArticleClick={openSummary} />
            </motion.div>
          ))}
        </motion.div>
      ) : (
        <div className="flex flex-col items-center py-24 text-center">
          <p className="text-sm text-zinc-500">No articles found.</p>
        </div>
      )}

      {/* ── Summary Modal ────────────────────────────────────────── */}
      <SummaryModal
        isOpen={isOpen}
        article={selectedArticle}
        summary={summary}
        loading={summaryLoading}
        error={summaryError}
        onClose={closeSummary}
      />
    </section>
  );
}
