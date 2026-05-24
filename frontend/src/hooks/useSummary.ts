/**
 * useSummary.ts — Summary State Hook
 * ====================================
 * Manages the full lifecycle of an article summary:
 *   - Which article is selected (modal open/closed)
 *   - Whether the summary is loading
 *   - The summary data (or error)
 *
 * USAGE:
 *   const {
 *     selectedArticle,
 *     isOpen,
 *     summary,
 *     loading,
 *     error,
 *     openSummary,
 *     closeSummary,
 *   } = useSummary();
 *
 *   <NewsCard onClick={() => openSummary(article)} />
 *   <SummaryModal isOpen={isOpen} onClose={closeSummary} ... />
 */

"use client";

import { useState, useCallback, useEffect } from "react";
import type { FeedArticle } from "@/services/api";
import {
  summarizeArticle,
  type SummaryResult,
  SummaryApiError,
} from "@/services/summarizer";

interface UseSummaryReturn {
  /** The article currently selected for summarization */
  selectedArticle: FeedArticle | null;
  /** Whether the modal is open */
  isOpen: boolean;
  /** The loaded summary data (null while loading) */
  summary: SummaryResult | null;
  /** Whether the summary request is in flight */
  loading: boolean;
  /** Error message if the summary failed */
  error: string | null;
  /** Open the modal and start fetching the summary */
  openSummary: (article: FeedArticle) => void;
  /** Close the modal and reset state */
  closeSummary: () => void;
}

export function useSummary(): UseSummaryReturn {
  const [selectedArticle, setSelectedArticle] = useState<FeedArticle | null>(
    null,
  );
  const [isOpen, setIsOpen] = useState(false);
  const [summary, setSummary] = useState<SummaryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const openSummary = useCallback((article: FeedArticle) => {
    setSelectedArticle(article);
    setIsOpen(true);
    setSummary(null);
    setError(null);
    setLoading(true);

    summarizeArticle(article)
      .then((data) => {
        setSummary(data);
        setError(null);
      })
      .catch((err) => {
        if (err instanceof SummaryApiError) {
          setError(err.detail);
        } else {
          setError("Failed to generate summary. Please try again.");
        }
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const closeSummary = useCallback(() => {
    setIsOpen(false);
    // Delay clearing article so exit animation can reference it
    setTimeout(() => {
      setSelectedArticle(null);
      setSummary(null);
      setError(null);
    }, 350);
  }, []);

  // Close on Escape key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && isOpen) {
        closeSummary();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, closeSummary]);

  return {
    selectedArticle,
    isOpen,
    summary,
    loading,
    error,
    openSummary,
    closeSummary,
  };
}
