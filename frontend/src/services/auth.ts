/**
 * services/auth.ts
 * =================
 * Pure-function auth API layer — zero state, no React dependencies.
 *
 * BACKEND CONTRACT (FastAPI):
 *   POST /auth/signup   { email, password, full_name? }  → MessageResponse
 *   POST /auth/login    { email, password }              → TokenResponse
 *   GET  /auth/me       Authorization: Bearer <token>    → UserResponse
 *   PUT  /auth/interests ?interests=AI&interests=tech    → UserResponse
 */

import { api, setStoredToken, removeStoredToken } from "./api";
import type {
  SignupPayload,
  LoginPayload,
  TokenResponse,
  UserResponse,
  MessageResponse,
} from "@/types/auth";

// ─── Endpoints ────────────────────────────────────────────────────────

const AUTH = {
  signup: "/auth/signup",
  login: "/auth/login",
  me: "/auth/me",
  interests: "/auth/interests",
} as const;

// ─── Public Functions ─────────────────────────────────────────────────

export async function signup(payload: SignupPayload): Promise<MessageResponse> {
  return api.post<MessageResponse>(AUTH.signup, payload, { noAuth: true });
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const token = await api.post<TokenResponse>(AUTH.login, payload, { noAuth: true });
  setStoredToken(token.access_token);
  return token;
}

export async function getMe(): Promise<UserResponse> {
  return api.get<UserResponse>(AUTH.me);
}

export async function updateInterests(interests: string[]): Promise<UserResponse> {
  return api.put<UserResponse>(AUTH.interests, undefined, {
    params: { interests },
  });
}

export function logout(): void {
  removeStoredToken();
}
