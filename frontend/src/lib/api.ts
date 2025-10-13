import { getToken } from "./auth";

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api";
  const token = getToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${base}${path}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = (data && data.detail) || "Request failed";
    throw new Error(detail);
  }
  return data as T;
}
