"use client";

export type StoredUser = {
  id: number;
  name: string;
  email: string;
};

const TOKEN_KEY = "gridcap_token";
const USER_KEY = "gridcap_user";
const LEAGUE_KEY = "gridcap_selected_league";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearAuth(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(LEAGUE_KEY);
}

export function setCurrentUser(user: StoredUser): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getCurrentUser(): StoredUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredUser;
  } catch (err) {
    return null;
  }
}

export function setSelectedLeague(leagueId: number): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(LEAGUE_KEY, leagueId.toString());
}

export function getSelectedLeague(): number | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(LEAGUE_KEY);
  if (!raw) return null;
  const parsed = Number(raw);
  return Number.isNaN(parsed) ? null : parsed;
}
