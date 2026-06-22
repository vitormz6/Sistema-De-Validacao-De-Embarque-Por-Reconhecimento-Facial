/**
 * Low-level token persistence — deliberately separate from `AuthContext`
 * (see `AuthProvider.tsx`) so `httpClient.ts` can read/clear the token
 * without importing React or creating a dependency cycle between the
 * HTTP layer and the auth module that uses it.
 */

const TOKEN_STORAGE_KEY = "admin-web.auth.token";

export function getStoredToken(): string | null {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string): void {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearAuthSession(): void {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}
