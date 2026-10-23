const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("avokatim_token");
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem("avokatim_token", token);
  else localStorage.removeItem("avokatim_token");
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
export const apiDelete = (path: string) => api(path, { method: "DELETE" });
export const apiUpload = <T = unknown>(path: string, form: FormData) =>
  api<T>(path, { method: "POST", body: form });

/** POST to a Server-Sent-Events endpoint and invoke onEvent per parsed event.
    Used by the assistant so long answers stream in without any timeout. */
export async function apiStream(
  path: string,
  body: unknown,
  onEvent: (event: Record<string, unknown>) => void
): Promise<void> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok || !res.body) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {}
    throw new ApiError(res.status, detail);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";
    for (const raw of events) {
      const line = raw.split("\n").find((l) => l.startsWith("data:"));
      if (!line) continue;
      try {
        onEvent(JSON.parse(line.slice(5).trim()));
      } catch {}
    }
  }
}

/** Download an authenticated file endpoint and trigger a save dialog. */
export async function apiDownload(
  path: string,
  filename: string,
  init?: { method?: string; body?: unknown }
): Promise<boolean> {
  const headers: Record<string, string> = { Authorization: `Bearer ${getToken()}` };
  if (init?.body !== undefined) headers["Content-Type"] = "application/json";
  const res = await fetch(`${API_BASE}${path}`, {
    method: init?.method || "GET",
    headers,
    body: init?.body === undefined ? undefined : JSON.stringify(init.body),
  });
  if (!res.ok) return false;
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
  return true;
}
