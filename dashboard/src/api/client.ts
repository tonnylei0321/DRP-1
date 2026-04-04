/**
 * API 客户端 — 大屏专用，与后端通信
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

let _token: string | null = localStorage.getItem('drp_token');

export function setToken(token: string) {
  _token = token;
  localStorage.setItem('drp_token', token);
}

export function clearToken() {
  _token = null;
  localStorage.removeItem('drp_token');
}

export function getToken(): string | null {
  return _token;
}

export async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (_token) headers['Authorization'] = `Bearer ${_token}`;

  const resp = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!resp.ok) {
    const text = await resp.text().catch(() => '');
    throw new Error(`${resp.status} ${resp.statusText}: ${text}`);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json() as Promise<T>;
}

export const authApi = {
  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string; expires_in: number }>(
      'POST', '/auth/login', { email, password }
    ),
};
