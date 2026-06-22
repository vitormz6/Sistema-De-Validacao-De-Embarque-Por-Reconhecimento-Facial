import axios, { type AxiosError } from "axios";

import { getStoredToken, clearAuthSession } from "@/modules/auth/authStorage";

/**
 * Single axios instance for every central-api call. Auth wiring lives
 * here rather than per-call: every authenticated request needs the same
 * Bearer header, and every 401 means the same thing — the token expired
 * or was revoked, so the session should be dropped and the user sent
 * back to /login.
 */
export const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

httpClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

httpClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      clearAuthSession();
      if (window.location.pathname !== "/login") {
        window.location.assign("/login");
      }
    }
    return Promise.reject(error);
  },
);

/**
 * central-api's `DomainError` handler (see app/core/exceptions.py)
 * always responds with `{"error": {"type": ..., "message": ...}}` —
 * this pulls the human-readable message out of that shape, falling back
 * to axios's own message for network-level failures (no response at all).
 */
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.error?.message;
    if (typeof detail === "string") {
      return detail;
    }
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Erro inesperado.";
}
