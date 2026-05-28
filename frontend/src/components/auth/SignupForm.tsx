"use client";

/**
 * components/auth/SignupForm.tsx
 * ===============================
 * Signup form — mirrors the same black & white glassmorphism aesthetic.
 * Validates: email format, password >= 8 chars, passwords match.
 */

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/services/api";

// ─── Animation Presets ────────────────────────────────────────────────

const ease = [0.25, 0.1, 0.25, 1.0] as const;

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease, delay: i * 0.06 },
  }),
};

const shake = {
  x: [0, -6, 6, -4, 4, 0],
  transition: { duration: 0.4 },
};

// ─── Input Style ──────────────────────────────────────────────────────

const inputStyle = {
  backgroundColor: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.08)",
  "--tw-ring-color": "rgba(255,255,255,0.15)",
} as React.CSSProperties;

const inputClass =
  "rounded-lg px-4 py-3 text-sm text-zinc-100 placeholder-zinc-600 outline-none transition-colors duration-200 focus:ring-1";

// ─── Component ────────────────────────────────────────────────────────

export function SignupForm() {
  const router = useRouter();
  const { signup } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError("Please fill in all required fields");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setSubmitting(true);
    try {
      await signup({
        email: email.trim(),
        password,
        full_name: fullName.trim() || undefined,
      });
      router.push("/");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.detail : "Something went wrong",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-5">
      {/* Ambient glow */}
      <div
        className="pointer-events-none fixed inset-0"
        style={{
          background:
            "radial-gradient(ellipse 50% 40% at 50% 35%, rgba(255,255,255,0.02) 0%, transparent 70%)",
        }}
      />

      <motion.div
        className="relative z-10 w-full max-w-[360px]"
        initial="hidden"
        animate="visible"
      >
        {/* ── Logo ──────────────────────────────────────────────── */}
        <motion.div
          custom={0}
          variants={fadeUp}
          className="mb-10 flex items-center justify-center gap-2.5"
        >
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
            className="text-sm font-semibold tracking-tight text-zinc-50"
            style={{ fontFamily: "var(--font-playfair), Georgia, serif" }}
          >
            Cognos
          </span>
        </motion.div>

        {/* ── Heading ───────────────────────────────────────────── */}
        <motion.h1
          custom={1}
          variants={fadeUp}
          className="mb-1.5 text-center text-2xl font-semibold tracking-tight text-zinc-50"
          style={{ fontFamily: "var(--font-playfair), Georgia, serif" }}
        >
          Create your account
        </motion.h1>

        <motion.p
          custom={2}
          variants={fadeUp}
          className="mb-8 text-center text-sm text-zinc-500"
        >
          Start getting smarter news recommendations
        </motion.p>

        {/* ── Error ─────────────────────────────────────────────── */}
        {error && (
          <motion.div
            animate={shake}
            className="mb-5 rounded-lg border px-4 py-3 text-sm text-red-300"
            style={{
              backgroundColor: "rgba(239,68,68,0.08)",
              borderColor: "rgba(239,68,68,0.15)",
            }}
          >
            {error}
          </motion.div>
        )}

        {/* ── Form ──────────────────────────────────────────────── */}
        <motion.form
          custom={3}
          variants={fadeUp}
          onSubmit={handleSubmit}
          className="flex flex-col gap-4"
        >
          {/* Full Name */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="signup-name"
              className="text-xs font-medium text-zinc-400"
            >
              Full name{" "}
              <span className="text-zinc-600">(optional)</span>
            </label>
            <input
              id="signup-name"
              type="text"
              autoComplete="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="John Doe"
              className={inputClass}
              style={inputStyle}
            />
          </div>

          {/* Email */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="signup-email"
              className="text-xs font-medium text-zinc-400"
            >
              Email
            </label>
            <input
              id="signup-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className={inputClass}
              style={inputStyle}
            />
          </div>

          {/* Password */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="signup-password"
              className="text-xs font-medium text-zinc-400"
            >
              Password
            </label>
            <input
              id="signup-password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 8 characters"
              className={inputClass}
              style={inputStyle}
            />
          </div>

          {/* Confirm Password */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="signup-confirm"
              className="text-xs font-medium text-zinc-400"
            >
              Confirm password
            </label>
            <input
              id="signup-confirm"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter your password"
              className={inputClass}
              style={inputStyle}
            />
          </div>

          {/* Submit */}
          <motion.button
            type="submit"
            disabled={submitting}
            className="mt-2 flex items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-all duration-200 disabled:opacity-50"
            style={{ backgroundColor: "#FAFAFA", color: "#09090B" }}
            whileHover={!submitting ? { backgroundColor: "#E4E4E7" } : {}}
            whileTap={!submitting ? { scale: 0.98 } : {}}
          >
            {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
            {submitting ? "Creating account..." : "Create account"}
          </motion.button>
        </motion.form>

        {/* ── Switch to login ───────────────────────────────────── */}
        <motion.p
          custom={4}
          variants={fadeUp}
          className="mt-8 text-center text-sm text-zinc-500"
        >
          Already have an account?{" "}
          <Link
            href="/login"
            className="text-zinc-300 transition-colors duration-200 hover:text-zinc-100"
          >
            Sign in
          </Link>
        </motion.p>
      </motion.div>
    </div>
  );
}
