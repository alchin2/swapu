/**
 * Auth utilities — stores JWT in localStorage, provides authenticated fetch wrapper.
 */

const TOKEN_KEY = "access_token";
const USER_KEY = "auth_user";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getUser(): { id: string; name: string; email: string } | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setAuth(token: string, user: { id: string; name: string; email: string }) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  // Keep guest_user_id in sync for backward compat
  localStorage.setItem("guest_user_id", user.id);
  window.dispatchEvent(new Event("auth_changed"));
  window.dispatchEvent(new Event("guest_user_changed"));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem("guest_user_id");
  window.dispatchEvent(new Event("auth_changed"));
  window.dispatchEvent(new Event("guest_user_changed"));
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

/**
 * Wrapper around fetch that automatically injects the Authorization header.
 * Falls through to regular fetch if no token is stored.
 */
export function authFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const token = getToken();
  const headers = new Headers(init?.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return fetch(input, { ...init, headers });
}
