"use client";

/**
 * page.tsx — Premium Landing + Feed Page
 * =======================================
 * Cinematic hero with background image, minimal navbar, and AI-powered news feed.
 * Vintage editorial aesthetic: black & white, serif typography, restraint.
 *
 * IMPORTANT: This file uses ONLY standard Tailwind zinc utilities
 * and inline styles with hex/rgba values. No custom theme classes
 * that might not be configured in Tailwind v4.
 */

import Image from "next/image";
import { Playfair_Display } from "next/font/google";
import { motion, useScroll, useTransform, type Variants } from "framer-motion";
import { FeedSection } from "@/components/feed/FeedSection";

// ─── Vintage Serif Font ────────────────────────────────────────────────

const playfair = Playfair_Display({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-playfair",
  weight: ["400", "500", "600", "700"],
});

// ─── Animation Presets ─────────────────────────────────────────────────
async function wakeBackend() {
  try {
    await wakeBackend();
    await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/health`
    );
  } catch (error) {
    console.log("Backend waking up...");
  }
}
const easeVal = [0.25, 0.1, 0.25, 1.0] as const;
const easeOutVal = [0.0, 0.0, 0.2, 1.0] as const;
const springVal = { type: "spring" as const, stiffness: 100, damping: 20 };

const stagger = {
  container: {
    hidden: {},
    visible: {
      transition: { staggerChildren: 0.15, delayChildren: 0.4 },
    },
  },
  item: {
    hidden: { opacity: 0, y: 24, filter: "blur(8px)" },
    visible: {
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      transition: { duration: 0.7, ease: easeOutVal },
    },
  },
} satisfies Record<string, Variants>;

const heroTextReveal = {
  hidden: { opacity: 0, y: 40, filter: "blur(12px)" },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: {
      duration: 1,
      ease: easeOutVal,
      delay: 0.3 + i * 0.15,
    },
  }),
} satisfies Variants;


// ─── Hero Background ──────────────────────────────────────────────────

function HeroBackground() {
  const { scrollY } = useScroll();
  const y = useTransform(scrollY, [0, 800], [0, 200]);
  const scale = useTransform(scrollY, [0, 800], [1, 1.1]);
  const opacity = useTransform(scrollY, [0, 500], [1, 0]);

  return (
    <motion.div className="absolute inset-0" style={{ y, scale, opacity }}>
      {/* Background Image */}
      <Image
        src="/images/image.jpg"
        alt=""
        fill
        priority
        className="object-cover"
        sizes="100vw"
      />
      {/* Multi-layer overlays for depth & readability */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(180deg, rgba(9,9,11,0.60) 0%, rgba(9,9,11,0.45) 40%, rgba(9,9,11,0.75) 70%, rgba(9,9,11,0.95) 100%)",
        }}
      />
      {/* Subtle white radial glow for editorial depth */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% 45%, rgba(255,255,255,0.04) 0%, transparent 70%)",
        }}
      />
      {/* Noise texture for film grain / vintage newsprint feel */}
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
        }}
      />
    </motion.div>
  );
}


// ─── Ambient Background (for feed section below hero) ─────────────────

function AmbientBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden">
      <motion.div
        className="absolute -right-32 -top-32 h-[600px] w-[600px] rounded-full opacity-[0.04]"
        style={{
          background:
            "radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%)",
        }}
        animate={{
          x: [0, 40, -20, 0],
          y: [0, -30, 20, 0],
          scale: [1, 1.05, 0.95, 1],
        }}
        transition={{
          duration: 20,
          ease: "easeInOut",
          repeat: Infinity,
          repeatType: "loop",
        }}
      />
      <motion.div
        className="absolute -bottom-48 -left-32 h-[500px] w-[500px] rounded-full opacity-[0.03]"
        style={{
          background:
            "radial-gradient(circle, rgba(255,255,255,0.12) 0%, transparent 70%)",
        }}
        animate={{
          x: [0, -30, 20, 0],
          y: [0, 20, -30, 0],
          scale: [1, 0.95, 1.05, 1],
        }}
        transition={{
          duration: 25,
          ease: "easeInOut",
          repeat: Infinity,
          repeatType: "loop",
        }}
      />
    </div>
  );
}


// ─── Navbar ───────────────────────────────────────────────────────────

function Navbar() {
  return (
    <motion.nav
      className="fixed left-0 right-0 top-0 z-50 flex items-center justify-between px-6 py-4 md:px-10"
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: easeOutVal, delay: 0.1 }}
    >
      {/* Glass backdrop */}
      <div
        className="absolute inset-0 border-x-0 border-t-0"
        style={{
          background: "rgba(9,9,11,0.6)",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          backdropFilter: "blur(24px) saturate(180%)",
          WebkitBackdropFilter: "blur(24px) saturate(180%)",
        }}
      />

      {/* Logo + Company Name */}
      <div className="relative z-10 flex items-center gap-2.5">
        <div
          className="flex h-8 w-8 items-center justify-center rounded-lg"
          style={{ backgroundColor: "#FAFAFA" }}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            style={{ color: "#09090B" }}
          >
            <path
              d="M8 1L14.5 5V11L8 15L1.5 11V5L8 1Z"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinejoin="round"
            />
            <circle cx="8" cy="8" r="2" fill="currentColor" />
          </svg>
        </div>
        <span
          className={`text-sm font-semibold tracking-tight text-zinc-50 ${playfair.variable}`}
          style={{ fontFamily: "var(--font-playfair), Georgia, serif" }}
        >
          Cognos
        </span>
      </div>

      {/* Right: Sign in + Get Access only */}
      <div className="relative z-10 flex items-center gap-3">
        <a
          href="#"
          className="text-sm text-zinc-400 transition-colors duration-300 hover:text-zinc-100"
        >
          Sign in
        </a>
        <motion.a
          href="#"
          className="rounded-lg px-4 py-2 text-sm font-medium transition-all duration-300"
          style={{
            backgroundColor: "#FAFAFA",
            color: "#09090B",
          }}
          whileHover={{
            backgroundColor: "#E4E4E7",
            boxShadow: "0 2px 12px rgba(255,255,255,0.1)",
          }}
          whileTap={{ scale: 0.97 }}
          transition={springVal}
        >
          Get Access
        </motion.a>
      </div>
    </motion.nav>
  );
}


// ─── Hero Section ─────────────────────────────────────────────────────

function Hero() {
  return (
    <section className="relative flex min-h-dvh items-center justify-center px-6 overflow-hidden">
      <HeroBackground />

      {/* Content */}
      <motion.div
        className="relative z-10 mx-auto max-w-4xl text-center"
        variants={stagger.container}
        initial="hidden"
        animate="visible"
      >
        {/* Eyebrow */}
        <motion.div variants={stagger.item} className="mb-8 inline-flex">
          <motion.span
            className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-medium"
            style={{
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.10)",
              backdropFilter: "blur(12px)",
              WebkitBackdropFilter: "blur(12px)",
              color: "#D4D4D8",
            }}
            whileHover={{
              background: "rgba(255,255,255,0.07)",
              borderColor: "rgba(255,255,255,0.20)",
            }}
            transition={{ duration: 0.3 }}
          >
            <span
              className="h-1.5 w-1.5 rounded-full animate-pulse"
              style={{ backgroundColor: "#FAFAFA" }}
            />
            AI-Powered Intelligence
          </motion.span>
        </motion.div>

        {/* Headline — vintage serif with staggered reveal */}
        <div className="mx-auto max-w-3xl overflow-hidden">
          <motion.h1
            className={`text-balance text-[2.5rem] font-semibold leading-[1.05] tracking-[-0.02em] text-zinc-50 sm:text-5xl md:text-6xl lg:text-7xl ${playfair.variable}`}
            style={{ fontFamily: "var(--font-playfair), Georgia, serif" }}
            initial="hidden"
            animate="visible"
          >
            <motion.span
              variants={heroTextReveal}
              custom={0}
              className="inline"
            >
              News that{" "}
            </motion.span>
            <motion.span
              variants={heroTextReveal}
              custom={1}
              className="inline bg-clip-text text-transparent"
              style={{
                backgroundImage:
                  "linear-gradient(135deg, #FFFFFF 0%, #E4E4E7 40%, #A1A1AA 80%, #71717A 100%)",
              }}
            >
              understands
            </motion.span>
            <motion.span
              variants={heroTextReveal}
              custom={2}
              className="inline"
            >
              {" "}what matters to you
            </motion.span>
          </motion.h1>
        </div>

        {/* Subheadline */}
        <motion.p
          variants={stagger.item}
          className="mx-auto mt-7 max-w-xl text-balance text-lg leading-relaxed text-zinc-400 md:text-xl"
        >
          Cognos reads thousands of sources, classifies every story with NLP,
          and surfaces only what&apos;s relevant to your interests. Not more news
          &mdash; smarter news.
        </motion.p>

        {/* Single CTA — Explore Feed */}
        <motion.div
          variants={stagger.item}
          className="mt-10 flex flex-col items-center justify-center"
        >
          <motion.a
            href="#feed"
            className="group relative inline-flex items-center gap-2.5 overflow-hidden rounded-2xl px-8 py-4 text-sm font-medium"
            style={{
              backgroundColor: "#FAFAFA",
              color: "#09090B",
              boxShadow: "0 0 0 0 rgba(255,255,255,0)",
            }}
            whileHover={{
              boxShadow: "0 8px 32px rgba(255,255,255,0.12), 0 0 0 1px rgba(255,255,255,0.08)",
              scale: 1.02,
            }}
            whileTap={{ scale: 0.98 }}
            transition={springVal}
          >
            {/* Shimmer effect on hover */}
            <span
              className="absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100"
              style={{
                background:
                  "linear-gradient(120deg, transparent 30%, rgba(0,0,0,0.06) 50%, transparent 70%)",
                backgroundSize: "200% 100%",
              }}
            />
            <span className="relative z-10">Explore Feed</span>
            <svg
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              className="relative z-10 transition-transform duration-300 group-hover:translate-x-0.5"
            >
              <path
                d="M1 7H13M13 7L7 1M13 7L7 13"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </motion.a>
        </motion.div>

        {/* Trust line */}
        <motion.div
          variants={stagger.item}
          className="mt-16 flex flex-col items-center gap-3"
        >
          <div className="flex -space-x-2">
            {[
              "rgba(255,255,255,0.12)",
              "rgba(255,255,255,0.10)",
              "rgba(255,255,255,0.14)",
              "rgba(255,255,255,0.08)",
            ].map((bg, i) => (
              <motion.div
                key={i}
                className="h-7 w-7 rounded-full"
                style={{
                  backgroundColor: bg,
                  border: "2px solid #09090B",
                }}
                whileHover={{ scale: 1.15, y: -2 }}
                transition={springVal}
              />
            ))}
          </div>
          
        </motion.div>
      </motion.div>

      {/* Scroll indicator */}
      <motion.div
        className="absolute bottom-8 left-1/2 z-10 -translate-x-1/2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2, duration: 1 }}
      >
        <motion.div
          className="flex h-9 w-5 items-start justify-center rounded-full p-1.5"
          style={{
            border: "1px solid rgba(255,255,255,0.10)",
            background: "rgba(255,255,255,0.03)",
          }}
          animate={{ y: [0, 5, 0] }}
          transition={{ duration: 2, ease: easeVal, repeat: Infinity }}
        >
          <motion.div
            className="h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: "rgba(255,255,255,0.5)" }}
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 2, ease: "easeInOut", repeat: Infinity }}
          />
        </motion.div>
      </motion.div>

      {/* Bottom gradient fade into feed */}
      <div
        className="absolute bottom-0 left-0 right-0 h-32"
        style={{
          background: "linear-gradient(to top, #09090B 0%, transparent 100%)",
        }}
      />
    </section>
  );
}


// ─── Page ─────────────────────────────────────────────────────────────

export default function Home() {
  return (
    <main
      className={`relative min-h-dvh overflow-hidden ${playfair.variable}`}
      style={{ backgroundColor: "#09090B" }}
    >
      <AmbientBackground />
      <Navbar />
      <Hero />
      <div id="feed">
        <FeedSection />
      </div>
    </main>
  );
}
