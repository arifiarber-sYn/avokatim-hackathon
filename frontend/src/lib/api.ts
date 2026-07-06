const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("boralaw_token");
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem("boralaw_token", token);
  else localStorage.removeItem("boralaw_token");
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function api<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401 && typeof window !== "undefined" && !path.startsWith("/auth")) {
    setToken(null);
    window.location.href = "/login";
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {}
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const apiGet = <T = unknown>(path: string) => api<T>(path);
export const apiPost = <T = unknown>(path: string, body?: unknown) =>
  api<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
export const apiPatch = <T = unknown>(path: string, body?: unknown) =>
  api<T>(path, { method: "PATCH", body: body === undefined ? undefined : JSON.stringify(body) });
export const apiPut = <T = unknown>(path: string, body?: unknown) =>
  api<T>(path, { method: "PUT", body: JSON.stringify(body) });
export const apiUpload = <T = unknown>(path: string, form: FormData) =>
  api<T>(path, { method: "POST", body: form });
