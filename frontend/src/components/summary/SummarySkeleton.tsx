"use client";

/**
 * SummarySkeleton.tsx
 * ===================
 * Luxury shimmer loading state for the summary modal.
 *
 * Not a basic gray pulse — this uses a gradient shimmer that
 * sweeps left-to-right, like light catching a polished surface.
 * Feels intentional and premium, not "loading spinner."
 */

export function SummarySkeleton() {
  return (
    <div className="space-y-5">
      {/* Reading time placeholder */}
      <div className="flex items-center gap-3">
        <div className="shimmer h-4 w-24 rounded" />
        <div className="shimmer h-4 w-16 rounded" />
      </div>

      {/* Summary bullets — 4 lines with varying widths */}
      <div className="space-y-3">
        {[
          "w-full",
          "w-11/12",
          "w-4/5",
          "w-9/12",
        ].map((width, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className="shimmer mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" />
            <div className={`shimmer h-4 rounded ${width}`} />
          </div>
        ))}
      </div>

      {/* Sentiment placeholder */}
      <div className="flex items-center gap-3 pt-2">
        <div className="shimmer h-6 w-24 rounded-full" />
        <div className="shimmer h-4 w-20 rounded" />
      </div>
    </div>
  );
}

/**
 * CSS for the shimmer effect.
 * Add this to globals.css or use as a Tailwind component.
 *
 * .shimmer {
 *   background: linear-gradient(
 *     90deg,
 *     rgba(255,255,255,0.03) 25%,
 *     rgba(255,255,255,0.08) 50%,
 *     rgba(255,255,255,0.03) 75%
 *   );
 *   background-size: 200% 100%;
 *   animation: shimmer 1.5s ease-in-out infinite;
 * }
 *
 * @keyframes shimmer {
 *   0%   { background-position: 200% 0; }
 *   100% { background-position: -200% 0; }
 * }
 */
