// src/styles/theme.ts

export const colors = {
  background: "#09090B",
  surface: "#111114",
  elevated: "#18181B",
  overlay: "#1E1E23",

  text: {
    primary: "#FAFAFA",
    secondary: "#A1A1AA",
    tertiary: "#71717A",
    disabled: "#3F3F46",
  },

  accent: {
    DEFAULT: "#8B5CF6",
    light: "#A78BFA",
    lighter: "#C4B5FD",
    dark: "#6D28D9",

    // tinted backgrounds
    ghost: "rgba(139, 92, 246, 0.08)",

    // borders / subtle highlights
    muted: "rgba(139, 92, 246, 0.15)",
  },

  success: "#34D399",
  warning: "#FBBF24",
  error: "#F87171",
  info: "#60A5FA",

  border: {
    // cards / panels
    DEFAULT: "rgba(255,255,255,0.08)",

    // separators
    subtle: "rgba(255,255,255,0.04)",

    // active states
    strong: "rgba(255,255,255,0.15)",
  },
} as const;


export const gradients = {
  brand:
    "linear-gradient(135deg, #8B5CF6 0%, #6D28D9 50%, #4C1D95 100%)",

  intelligence:
    "linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%)",

  surface:
    "linear-gradient(180deg, rgba(255,255,255,0.02) 0%, transparent 100%)",

  fadeDown:
    "linear-gradient(180deg, transparent 0%, #09090B 100%)",

  fadeUp:
    "linear-gradient(0deg, transparent 0%, #09090B 100%)",

  accentGlow:
    "linear-gradient(135deg, rgba(139,92,246,0.3), rgba(139,92,246,0))",
} as const;


export const fonts = {
  sans:
    "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",

  mono:
    "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace",
} as const;


export const fontSizes = {
  display: {
    "2xl": {
      size: "4.5rem",
      lineHeight: "1.05",
      letterSpacing: "-0.03em",
      weight: 600,
    },

    xl: {
      size: "3.75rem",
      lineHeight: "1.08",
      letterSpacing: "-0.025em",
      weight: 600,
    },

    lg: {
      size: "3rem",
      lineHeight: "1.1",
      letterSpacing: "-0.02em",
      weight: 600,
    },

    md: {
      size: "2.25rem",
      lineHeight: "1.15",
      letterSpacing: "-0.015em",
      weight: 600,
    },

    sm: {
      size: "1.875rem",
      lineHeight: "1.2",
      letterSpacing: "-0.01em",
      weight: 600,
    },
  },

  ui: {
    xl: {
      size: "1.25rem",
      lineHeight: "1.5",
      letterSpacing: "-0.01em",
      weight: 500,
    },

    lg: {
      size: "1.125rem",
      lineHeight: "1.5",
      letterSpacing: "-0.005em",
      weight: 500,
    },

    md: {
      size: "1rem",
      lineHeight: "1.6",
      letterSpacing: "0",
      weight: 400,
    },

    sm: {
      size: "0.875rem",
      lineHeight: "1.6",
      letterSpacing: "0.005em",
      weight: 400,
    },

    xs: {
      size: "0.75rem",
      lineHeight: "1.5",
      letterSpacing: "0.01em",
      weight: 500,
    },

    "2xs": {
      size: "0.6875rem",
      lineHeight: "1.4",
      letterSpacing: "0.02em",
      weight: 600,
    },
  },
} as const;


export const spacing = {
  0: "0px",
  0.5: "2px",
  1: "4px",
  1.5: "6px",
  2: "8px",
  3: "12px",
  4: "16px",
  5: "20px",
  6: "24px",
  8: "32px",
  10: "40px",
  12: "48px",
  16: "64px",
  20: "80px",
  24: "96px",
  32: "128px",
} as const;


export const radius = {
  sm: "6px",
  md: "8px",
  lg: "12px",
  xl: "16px",
  "2xl": "20px",
  "3xl": "24px",
  full: "9999px",
} as const;


export const glass = {
  sm: {
    bg: "rgba(255,255,255,0.03)",
    border: "rgba(255,255,255,0.06)",
    blur: "blur(8px)",
    shadow: "0 1px 2px rgba(0,0,0,0.3)",
  },

  md: {
    bg: "rgba(255,255,255,0.05)",
    border: "rgba(255,255,255,0.08)",
    blur: "blur(16px)",
    shadow: "0 4px 16px rgba(0,0,0,0.25)",
  },

  lg: {
    bg: "rgba(255,255,255,0.07)",
    border: "rgba(255,255,255,0.10)",
    blur: "blur(24px)",
    shadow: "0 8px 32px rgba(0,0,0,0.3)",
  },

  xl: {
    bg: "rgba(255,255,255,0.10)",
    border: "rgba(255,255,255,0.12)",
    blur: "blur(40px)",
    shadow: "0 16px 48px rgba(0,0,0,0.35)",
  },
} as const;


export const shadows = {
  xs: "0 1px 2px rgba(0,0,0,0.2)",

  sm:
    "0 2px 8px rgba(0,0,0,0.2), 0 1px 2px rgba(0,0,0,0.15)",

  md:
    "0 4px 16px rgba(0,0,0,0.25), 0 1px 4px rgba(0,0,0,0.15)",

  lg:
    "0 8px 32px rgba(0,0,0,0.3), 0 2px 8px rgba(0,0,0,0.2)",

  xl:
    "0 16px 48px rgba(0,0,0,0.35), 0 4px 16px rgba(0,0,0,0.2)",

  accent: {
    sm: "0 2px 8px rgba(139,92,246,0.15)",
    md: "0 4px 16px rgba(139,92,246,0.2)",
    lg: "0 8px 32px rgba(139,92,246,0.25)",
  },
} as const;


export const duration = {
  instant: 100,
  fast: 150,
  normal: 250,
  slow: 350,
  deliberate: 500,
} as const;


export const easing = {
  ease: [0.25, 0.1, 0.25, 1.0],
  easeOut: [0.0, 0.0, 0.2, 1.0],
  easeIn: [0.4, 0.0, 1.0, 1.0],
  easeInOut: [0.4, 0.0, 0.2, 1.0],
} as const;


export const spring = {
  gentle: {
    type: "spring",
    stiffness: 120,
    damping: 20,
    mass: 1,
  },

  snappy: {
    type: "spring",
    stiffness: 300,
    damping: 25,
    mass: 0.8,
  },

  bouncy: {
    type: "spring",
    stiffness: 400,
    damping: 15,
    mass: 0.6,
  },

  heavy: {
    type: "spring",
    stiffness: 200,
    damping: 30,
    mass: 1.2,
  },
} as const;


export const transitions = {
  fast: {
    duration: duration.fast,
    ease: easing.easeOut,
  },

  normal: {
    duration: duration.normal,
    ease: easing.ease,
  },

  slow: {
    duration: duration.slow,
    ease: easing.easeInOut,
  },

  spring: spring.gentle,
  snappy: spring.snappy,
} as const;


export const zIndex = {
  base: 0,
  dropdown: 10,
  sticky: 20,
  overlay: 30,
  modal: 40,
  popover: 50,
  toast: 60,
  tooltip: 70,
} as const;


export const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  "2xl": 1536,
} as const;