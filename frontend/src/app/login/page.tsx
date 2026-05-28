"use client";

import { GuestGuard } from "@/lib/protected-route";
import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <GuestGuard>
      <main style={{ backgroundColor: "#09090B" }} className="min-h-screen">
        <LoginForm />
      </main>
    </GuestGuard>
  );
}
