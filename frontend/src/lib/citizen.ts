// Citizen-side API client (marketplace). Citizens have their own token,
// separate from the lawyer app token and the portal token.

const KEY = "avokatim_citizen_token";

export function getCitizenToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(KEY);
}

export function setCitizenToken(token: string | null) {
  if (token) localStorage.setItem(KEY, token);
  else localStorage.removeItem(KEY);
}

export async function citizenApi<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  const token = getCitizenToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body) headers["Content-Type"] = "application/json";
  const res = await fetch(`/api/public${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {}
    const err = new Error(detail) as Error & { status?: number };
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const citizenGet = <T = unknown>(path: string) => citizenApi<T>(path);
export const citizenPost = <T = unknown>(path: string, body?: unknown) =>
  citizenApi<T>(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
  });

export interface CitizenInfo {
  id: string;
  full_name: string;
  email: string;
  phone: string | null;
  locale: string;
  email_verified: boolean;
}

export interface CitizenCase {
  id: string;
  category: string;
  description: string;
  city: string | null;
  urgency: string;
  status: string;
  directed: boolean;
  claimed_by: string | null;
  claimed_at: string | null;
  closed_reason: string | null;
  created_at: string;
}

export interface PublicLawyer {
  id: string;
  tenant_id: string;
  full_name: string;
  firm_name: string;
  bio: string | null;
  practice_areas: string[];
  cities: string[];
  languages: string[];
  photo: string | null;
}
