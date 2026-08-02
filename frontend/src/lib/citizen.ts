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

/** Multipart upload with the citizen token (no JSON content-type). */
export async function citizenUpload<T = unknown>(path: string, form: FormData): Promise<T> {
  const headers: Record<string, string> = {};
  const token = getCitizenToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`/api/public${path}`, { method: "POST", headers, body: form });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {}
    const err = new Error(detail) as Error & { status?: number };
    err.status = res.status;
    throw err;
  }
  return res.json();
}

/** Download an authenticated citizen file endpoint. */
export async function citizenDownload(path: string, filename: string): Promise<boolean> {
  const token = getCitizenToken();
  const res = await fetch(`/api/public${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
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
  /** Data-URL avatar from social login (D-058); null for email accounts. */
  photo: string | null;
  /** Social-login provider (google/apple/meta) or null for email accounts. */
  provider: string | null;
}

/** Remembered account for one-tap re-login after logout (D-058) — the
    Google/Clio "Continue as X" pattern. Never contains a token, only what
    the login screen shows: name, email, photo and which provider to hint. */
export interface LastAccount {
  name: string;
  email: string;
  photo: string | null;
  provider: string | null;
}

const LAST_ACCOUNT_KEY = "avokatim_last_account";

export function getLastAccount(): LastAccount | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(LAST_ACCOUNT_KEY);
    if (!raw) return null;
    const a = JSON.parse(raw) as LastAccount;
    return a && a.email ? a : null;
  } catch {
    return null;
  }
}

export function rememberCitizen(c: CitizenInfo) {
  try {
    localStorage.setItem(
      LAST_ACCOUNT_KEY,
      JSON.stringify({
        name: c.full_name,
        email: c.email,
        photo: c.photo,
        provider: c.provider,
      } satisfies LastAccount),
    );
  } catch {
    // A photo data-URL can overflow the localStorage quota — remember the
    // account without it rather than not at all
    try {
      localStorage.setItem(
        LAST_ACCOUNT_KEY,
        JSON.stringify({ name: c.full_name, email: c.email, photo: null, provider: c.provider }),
      );
    } catch {}
  }
}

export function clearLastAccount() {
  localStorage.removeItem(LAST_ACCOUNT_KEY);
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
  // Last state change — used as the "matter opened"/"closed" timeline date
  updated_at?: string | null;
  // Reviews: set by /citizen/cases once the engagement concluded
  reviewed?: boolean;
  can_review?: boolean;
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
  // Paid-plan perk: sorted first and softly emphasized in the directory
  highlighted?: boolean;
  // Trust signals: OAK verification, client reviews, transparent pricing
  verified?: boolean;
  // One of the first verified offices (permanent early-adopter badge)
  founder?: boolean;
  consult_fee_eur?: number | null;
  rating?: number | null;
  review_count?: number;
  // Consultation booking enabled (Phase 4)
  booking?: boolean;
  // Trust signals (2026): years practicing + verified platform activity
  years_experience?: number | null;
  cases_completed?: number;
  // Public flat-fee service menu (transparent pricing)
  flat_services?: { title: string; price_eur: number }[];
}
