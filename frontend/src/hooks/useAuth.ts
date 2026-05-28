/**
 * hooks/useAuth.ts
 * =================
 * Public hook — re-exports the context consumer so components
 * don't need to know where the context file lives.
 *
 * Usage:
 *   const { user, loading, login, logout } = useAuth();
 */

export { useAuthContext as useAuth } from "@/context/AuthContext";
