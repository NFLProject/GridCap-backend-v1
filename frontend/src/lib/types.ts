export type AuthResponse = {
  id: number;
  name: string;
  email: string;
  token: string;
};

export type MeResponse = {
  id: number;
  name: string;
  email: string;
  created_at?: string;
};

export type League = {
  league_id: number;
  name: string;
};

export type Player = {
  id: number;
  name: string;
  position: string;
  team: string;
  cost: number;
};

export type Squad = {
  squad_id: number;
  league_id: number;
  budget_used: number;
  players: Player[];
};

export type SquadSaveResponse = Squad | null;

export type LineupRequest = {
  league_id: number;
  gw: number;
  starters: number[];
  captain: number;
  vice: number;
};

export type Standing = {
  team_name: string;
  points: number;
};
