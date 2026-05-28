/**
 * types/auth.ts
 * =============
 * TypeScript contracts mirroring the FastAPI Pydantic schemas.
 * When the backend schema changes, update here first.
 */

// ─── Request Payloads ─────────────────────────────────────────────────

export interface SignupPayload {
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

// ─── Response Shapes ──────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  interests: string | null;
}

export interface MessageResponse {
  message: string;
  detail: Record<string, unknown> | null;
}

export interface ApiErrorResponse {
  detail: string;
}

// ─── Auth Context Shape ───────────────────────────────────────────────

export interface AuthContextValue {
  user: UserResponse | null;
  loading: boolean;
  error: string | null;
  login: (payload: LoginPayload) => Promise<UserResponse>;
  signup: (payload: SignupPayload) => Promise<UserResponse>;
  logout: () => void;
  clearError: () => void;
}
