import axios from "axios";

/**
 * No auth header here — edge-api's `/local/*` endpoints are
 * unauthenticated by design (RFC scope: trusted local network on the
 * bus, no operator login). See edge-api.md for that decision.
 */
export const httpClient = axios.create({
  baseURL: import.meta.env.VITE_EDGE_API_BASE_URL,
  timeout: 15_000,
});

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
