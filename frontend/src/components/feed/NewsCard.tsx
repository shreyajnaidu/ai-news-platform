"use client";

/**
 * NewsCard.tsx
 * ============
 * Premium article card with subtle 3D tilt on hover.
 *
 * 3D TILT MECHANIC:
 *   - onMouseMove: calculate mouse position relative to card center
 *   - Apply rotateX/rotateY via Framer Motion with perspective
 *   - onMouseLeave: spring back to flat
 *   - Max tilt: 4 degrees (subtle, not theatrical)
 *
 * CLICK HANDLING:
 *   - onClick calls onArticleClick(article) to open the summary modal
 *   - The card is a <button> for accessibility, styled as a card
 *   - The external link is inside the summary modal CTA instead
 */

import { useRef, type MouseEvent } from "react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import type { FeedArticle } from "@/services/api";
import { tiltTransition } from "@/lib/animations";

// ─── Types ────────────────────────────────────────────────────────────

interface NewsCardProps {
  article: FeedArticle;
  onArticleClick: (article: FeedArticle) => void;
}

// ─── Helpers ──────────────────────────────────────────────────────────

const TILT_MAX = 4;

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

function scoreColor(score: number): string {
  if (score >= 80) return "#8B5CF6";
  if (score >= 50) return "rgba(167, 139, 250, 0.4)";
  return "#3F3F46";
}

// ─── NewsCard ─────────────────────────────────────────────────────────

export function NewsCard({ article, onArticleClick }: NewsCardProps) {
  const ref = useRef<HTMLButtonElement>(null);
  const time = formatTime(article.published_at);

  // ── 3D Tilt motion values ──────────────────────────────────────────
  // raw = the un-smoothed value from mouse position
  // spring = the smoothed value that the DOM actually renders
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const springConfig = { stiffness: 250, damping: 20, mass: 0.6 };
  const rotateX = useSpring(
    useTransform(mouseY, [-0.5, 0.5], [TILT_MAX, -TILT_MAX]),
    springConfig,
  );
  const rotateY = useSpring(
    useTransform(mouseX, [-0.5, 0.5], [-TILT_MAX, TILT_MAX]),
    springConfig,
  );

  function handleMouseMove(e: MouseEvent) {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5; // -0.5 to 0.5
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    mouseX.set(x);
    mouseY.set(y);
  }

  function handleMouseLeave() {
    mouseX.set(0);
    mouseY.set(0);
  }

  return (
    <motion.button
      ref={ref}
      type="button"
      onClick={() => onArticleClick(article)}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="group relative w-full cursor-pointer overflow-hidden rounded-xl text-left"
      style={{
        // 3D perspective container
        perspective: 800,
        backgroundColor: "#18181B",
        border: "1px solid rgba(255,255,255,0.08)",
        transformStyle: "preserve-3d",
      }}
      // Apply the 3D rotation
      whileHover={{
        boxShadow: "0 4px 12px rgba(139,92,246,0.08)",
      }}
      transition={{ duration: 0.2 }}
    >
      {/* The actual tilted element */}
      <motion.div
        style={{
          rotateX,
          rotateY,
          transformStyle: "preserve-3d",
        }}
        transition={tiltTransition}
      >
        {/* ── Surface gradient overlay ─────────────────────────────── */}
        <div
          className="pointer-events-none absolute inset-0 z-0"
          style={{
            background:
              "linear-gradient(180deg, rgba(255,255,255,0.015) 0%, transparent 40%)",
          }}
        />

        {/* ── Border hover effect ──────────────────────────────────── */}
        <div
          className="pointer-events-none absolute inset-0 z-20 rounded-xl transition-colors duration-200"
          style={{
            border: "1px solid transparent",
          }}
          // We handle hover border via CSS group-hover
        />

        {/* ── Image ─────────────────────────────────────────────────── */}
        <div
          className="relative aspect-[16/9] w-full overflow-hidden"
          style={{ backgroundColor: "#111114" }}
        >
          {article.image_url ? (
            <img
              src={article.image_url}
              alt=""
              className="h-full w-full object-cover transition-transform duration-500 ease-out group-hover:scale-[1.03]"
              loading="lazy"
            />
          ) : (
            <div
              className="h-full w-full"
              style={{
                background:
                  "linear-gradient(135deg, rgba(255,255,255,0.02) 0%, rgba(139,92,246,0.04) 100%)",
              }}
            />
          )}

          {/* Score indicator */}
          <div
            className="absolute right-3 top-3 z-10 flex items-center gap-1.5 rounded-full px-2.5 py-1 backdrop-blur-sm"
            style={{
              backgroundColor: "rgba(9,9,11,0.7)",
            }}
          >
            <span
              className="h-1.5 w-1.5 rounded-full"
              style={{ backgroundColor: scoreColor(article.score) }}
            />
            <span className="text-[10px] font-medium text-zinc-400">
              {Math.round(article.score)}
            </span>
          </div>
        </div>

        {/* ── Content ──────────────────────────────────────────────── */}
        <div className="relative z-10 p-5">
          {/* Category pill */}
          {article.category && (
            <span
              className="mb-3 inline-block rounded-full px-2.5 py-0.5 text-[11px] font-medium leading-none"
              style={{
                backgroundColor: "rgba(139,92,246,0.08)",
                color: "#A78BFA",
              }}
            >
              {article.category}
            </span>
          )}

          {/* Title */}
          <h3
            className="mb-2 text-[15px] font-semibold leading-snug tracking-[-0.01em] line-clamp-2"
            style={{ color: "#FAFAFA" }}
          >
            {article.title}
          </h3>

          {/* Description */}
          {article.description && (
            <p className="mb-3 text-sm leading-relaxed text-zinc-400 line-clamp-2">
              {article.description}
            </p>
          )}

          {/* Source + time */}
          <div className="flex items-center gap-2 text-[11px] text-zinc-500">
            {article.source && (
              <>
                <span className="font-medium text-zinc-500">
                  {article.source}
                </span>
                <span className="text-zinc-700">·</span>
              </>
            )}
            {time && <span>{time}</span>}
          </div>
        </div>
      </motion.div>
    </motion.button>
  );
}
