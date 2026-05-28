"use client";

import { GuestGuard } from "@/lib/protected-route";
import { SignupForm } from "@/components/auth/SignupForm";

export default function SignupPage() {
  return (
    <GuestGuard>
      <main style={{ backgroundColor: "#09090B" }} className="min-h-screen">
        <SignupForm />
      </main>
    </GuestGuard>
  );
}
