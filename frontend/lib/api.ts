export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";

export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type Task = {
  id: number;
  task_id: string;
  url: string;
  domain: string;
  platform?: string | null;
  task_type: string;
  status: string;
  progress: number;
  title?: string | null;
  filename?: string | null;
  file_size?: number | null;
  file_id?: number | null;
  error_message?: string | null;
  cancelled_at?: string | null;
  expired_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type User = {
  id: number;
  koyun_user_id: string;
  email?: string | null;
  username: string;
  avatar?: string | null;
  role: string;
  status: string;
  daily_quota: number;
  used_today: number;
};

export function getToken() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("koyun_token") || "";
}

export function setToken(token: string) {
  localStorage.setItem("koyun_token", token);
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers
    },
    cache: "no-store"
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message || body?.detail || `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export function formatBytes(value?: number | null) {
  if (!value) return "-";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = value;
  let unit = 0;
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024;
    unit += 1;
  }
  return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[unit]}`;
}

export function fmtTime(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}
