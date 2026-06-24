"use client";

/**
 * components/ui/sonner.tsx
 * =========================
 * Toast notification wrapper (shadcn/ui + Sonner).
 *
 * Styled for the always-dark aesthetic — no reliance on
 * CSS variable theme switching. Black & white glassmorphism.
 */

import { Toaster as Sonner } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

function Toaster({ ...props }: ToasterProps) {
  return (
    <Sonner
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast !bg-zinc-900 !text-zinc-100 !border-zinc-800 shadow-lg",
          description: "!text-zinc-400",
          actionButton:
            "!bg-zinc-50 !text-zinc-900",
          cancelButton:
            "!bg-zinc-800 !text-zinc-400",
          success: "!text-emerald-300",
          error: "!text-red-300",
        },
      }}
      {...props}
    />
  );
}

export { Toaster };
