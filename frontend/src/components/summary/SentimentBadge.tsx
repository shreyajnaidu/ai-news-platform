"use client";

/**
 * SentimentBadge.tsx
 * ==================
 * Displays the article's sentiment as a subtle, premium pill.
 *
 * Three states:
 *   positive  → green dot + "Positive"
 *   negative  → red dot + "Negative"
 *   neutral   → zinc dot + "Neutral"
 *
 * The dot is 6px — a period, not a lantern. The text is 11px.
 * The background is a tinted glass pill. Premium, restrained.
 */

interface SentimentBadgeProps {
  sentiment: string;
}

const sentimentConfig: Record<
  string,
  { dotColor: string; label: string; bgStyle: React.CSSProperties }
> = {
  positive: {
    dotColor: "#34D399",
    label: "Positive",
    bgStyle: {
      backgroundColor: "rgba(52, 211, 153, 0.08)",
      borderColor: "rgba(52, 211, 153, 0.15)",
    },
  },
  negative: {
    dotColor: "#F87171",
    label: "Negative",
    bgStyle: {
      backgroundColor: "rgba(248, 113, 113, 0.08)",
      borderColor: "rgba(248, 113, 113, 0.15)",
    },
  },
  neutral: {
    dotColor: "#71717A",
    label: "Neutral",
    bgStyle: {
      backgroundColor: "rgba(113, 113, 122, 0.08)",
      borderColor: "rgba(113, 113, 122, 0.12)",
    },
  },
};

export function SentimentBadge({ sentiment }: SentimentBadgeProps) {
  const key = sentiment.toLowerCase();
  const config = sentimentConfig[key] ?? sentimentConfig.neutral;

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium"
      style={{
        ...config.bgStyle,
        color: config.dotColor,
      }}
    >
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: config.dotColor }}
      />
      {config.label}
    </span>
  );
}
