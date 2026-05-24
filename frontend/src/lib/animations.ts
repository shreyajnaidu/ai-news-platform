/**
 * animations.ts — Reusable Motion Presets
 * ========================================
 * Every animation constant lives here so components never invent
 * their own timing, easing, or transform values.
 *
 * RULES (from the design philosophy "Respond, don't perform"):
 *   - Max translateY: 20px  (anything more feels theatrical)
 *   - Max scale: 1.05       (anything more feels bouncy/cheap)
 *   - Max rotateX/Y: 6deg   (anything more feels like a gimmick)
 *   - Max blur: 8px         (anything more obscures content)
 *   - Max duration: 0.5s    (anything more feels sluggish)
 */

import type { Variants, Transition } from "framer-motion";

// ─── Easing Curves ────────────────────────────────────────────────────

export const ease = {
  /** Apple's signature — the default for most UI motion */
  default: [0.25, 0.1, 0.25, 1.0] as const,
  /** Decelerates into place (like a car braking smoothly) */
  out: [0.0, 0.0, 0.2, 1.0] as const,
  /** Accelerates away (like a car pulling out) */
  in: [0.4, 0.0, 1.0, 1.0] as const,
  /** Slow start, fast middle, slow end */
  inOut: [0.4, 0.0, 0.2, 1.0] as const,
};

// ─── Duration ─────────────────────────────────────────────────────────

export const dur = {
  instant: 0.1,
  fast: 0.15,
  normal: 0.25,
  slow: 0.35,
  deliberate: 0.5,
};

// ─── Reusable Transitions ─────────────────────────────────────────────

export const transition = {
  fast: { duration: dur.fast, ease: ease.out } satisfies Transition,
  normal: { duration: dur.normal, ease: ease.default } satisfies Transition,
  slow: { duration: dur.slow, ease: ease.inOut } satisfies Transition,
  spring: {
    type: "spring" as const,
    stiffness: 120,
    damping: 20,
    mass: 1,
  } satisfies Transition,
  springSnappy: {
    type: "spring" as const,
    stiffness: 300,
    damping: 25,
    mass: 0.8,
  } satisfies Transition,
};

// ─── Fade + Slide Presets ─────────────────────────────────────────────

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: transition.normal,
  },
};

export const fadeDown: Variants = {
  hidden: { opacity: 0, y: -12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: transition.normal,
  },
};

/** Blur-to-sharp entrance — the Apple technique */
export const blurIn: Variants = {
  hidden: { opacity: 0, y: 16, filter: "blur(4px)" },
  visible: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { duration: 0.45, ease: ease.out },
  },
};

// ─── Stagger Systems ──────────────────────────────────────────────────

/** Card grid stagger — 60ms between items */
export const staggerGrid: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.06 },
  },
};

/** Section content stagger — 100ms between items */
export const staggerContent: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.1, delayChildren: 0.15 },
  },
};

// ─── Modal Presets ────────────────────────────────────────────────────

export const modalBackdrop: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: dur.slow } },
  exit: { opacity: 0, transition: { duration: dur.fast } },
};

export const modalContent: Variants = {
  hidden: { opacity: 0, scale: 0.96, y: 12 },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { duration: dur.slow, ease: ease.out },
  },
  exit: {
    opacity: 0,
    scale: 0.97,
    y: 8,
    transition: { duration: dur.fast, ease: ease.in },
  },
};

// ─── 3D Card Tilt ─────────────────────────────────────────────────────

/** Max tilt in degrees — keeps the effect subtle */
const TILT_MAX = 4;

/**
 * Calculate 3D tilt values from mouse position.
 * Returns rotateX and rotateY for perspective transform.
 *
 * The math: mouse position relative to card center, scaled
 * to ±TILT_MAX degrees. Closer to the edge = more tilt.
 */
export function calcTilt(
  mouseX: number,
  mouseY: number,
  cardWidth: number,
  cardHeight: number,
): { rotateX: number; rotateY: number } {
  const centerX = cardWidth / 2;
  const centerY = cardHeight / 2;
  const percentX = (mouseX - centerX) / centerX; // -1 to 1
  const percentY = (mouseY - centerY) / centerY; // -1 to 1

  return {
    // rotateX: positive = top tilts toward viewer (mouse below center)
    rotateX: -percentY * TILT_MAX,
    // rotateY: positive = right side tilts toward viewer (mouse right of center)
    rotateY: percentX * TILT_MAX,
  };
}

/** The reset state when the mouse leaves the card */
export const tiltReset = { rotateX: 0, rotateY: 0 };

/** Transition for the 3D tilt — spring feels more physical */
export const tiltTransition: Transition = {
  type: "spring",
  stiffness: 250,
  damping: 20,
  mass: 0.6,
};