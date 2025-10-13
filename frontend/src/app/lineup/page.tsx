"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import Button from "../../components/Button";
import Card from "../../components/Card";
import { api } from "../../lib/api";
import { getSelectedLeague, getToken } from "../../lib/auth";
import type { LineupRequest, Player, SquadSaveResponse } from "../../lib/types";

const STARTERS_REQUIRED = 9;

export default function LineupPage() {
  const router = useRouter();
  const [players, setPlayers] = useState<Player[]>([]);
  const [starters, setStarters] = useState<number[]>([]);
  const [captain, setCaptain] = useState<number | null>(null);
  const [vice, setVice] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const leagueId = getSelectedLeague();

  useEffect(() => {
    if (!getToken()) {
      router.replace("/");
      return;
    }
    if (!leagueId) {
      router.replace("/dashboard");
      return;
    }
    const load = async () => {
      try {
        const squad = await api<SquadSaveResponse>(`/squad?league_id=${leagueId}`);
        if (!squad || !squad.players) {
          setError("You need to save a squad first.");
          return;
        }
        setPlayers(squad.players);
      } catch (err) {
        setError((err as Error).message);
      }
    };
    load();
  }, [leagueId, router]);

  useEffect(() => {
    if (starters.length > STARTERS_REQUIRED) {
      setStarters((prev) => prev.slice(0, STARTERS_REQUIRED));
    }
  }, [starters.length]);

  useEffect(() => {
    if (captain && !starters.includes(captain)) {
      setCaptain(null);
    }
    if (vice && !starters.includes(vice)) {
      setVice(null);
    }
  }, [captain, vice, starters]);

  const toggleStarter = (playerId: number) => {
    setError(null);
    setSuccess(null);
    setStarters((prev) => {
      if (prev.includes(playerId)) {
        return prev.filter((id) => id !== playerId);
      }
      if (prev.length >= STARTERS_REQUIRED) {
        setError(`Select exactly ${STARTERS_REQUIRED} starters.`);
        return prev;
      }
      return [...prev, playerId];
    });
  };

  const handleSave = async () => {
    if (!leagueId) return;
    if (starters.length !== STARTERS_REQUIRED || !captain || !vice) {
      setError("Choose 9 starters plus captain and vice.");
      return;
    }
    if (captain === vice) {
      setError("Captain and vice must be different players.");
      return;
    }
    const payload: LineupRequest = {
      league_id: leagueId,
      gw: 1,
      starters,
      captain,
      vice,
    };
    try {
      await api("/lineup/set", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setSuccess("Lineup saved! Check the standings to see results.");
      router.push(`/standings/${leagueId}`);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const starterPlayers = useMemo(
    () => starters.map((id) => players.find((p) => p.id === id)).filter((p): p is Player => Boolean(p)),
    [players, starters]
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl mb-2">Set your lineup</h1>
        <p className="text-slate-600">Choose {STARTERS_REQUIRED} starters and assign captain &amp; vice.</p>
        {error && <p className="text-red-600 mt-2">{error}</p>}
        {success && <p className="text-green-600 mt-2">{success}</p>}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card title="Squad">
          <ul className="space-y-2 max-h-96 overflow-y-auto pr-2">
            {players.map((player) => {
              const selected = starters.includes(player.id);
              return (
                <li key={player.id}>
                  <button
                    type="button"
                    onClick={() => toggleStarter(player.id)}
                    className={`w-full flex justify-between items-center px-3 py-2 rounded border ${
                      selected ? "border-brand bg-sky-50" : "border-slate-200"
                    }`}
                  >
                    <span>
                      {player.name} <span className="text-xs text-slate-500">{player.position}</span>
                    </span>
                    <span className="font-semibold">${player.cost.toFixed(1)}m</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </Card>
        <Card title="Starters">
          <ul className="space-y-2">
            {starterPlayers.map((player) => (
              <li key={player.id} className="flex justify-between items-center">
                <span>
                  {player.name} <span className="text-xs text-slate-500">{player.position}</span>
                </span>
                <span className="font-semibold">${player.cost.toFixed(1)}m</span>
              </li>
            ))}
          </ul>
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div>
              <label className="text-sm font-medium text-slate-700" htmlFor="captain-select">
                Captain
              </label>
              <select
                id="captain-select"
                value={captain ?? ""}
                onChange={(event) => setCaptain(Number(event.target.value) || null)}
              >
                <option value="">Select</option>
                {starterPlayers.map((player) => (
                  <option key={player.id} value={player.id}>
                    {player.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700" htmlFor="vice-select">
                Vice Captain
              </label>
              <select id="vice-select" value={vice ?? ""} onChange={(event) => setVice(Number(event.target.value) || null)}>
                <option value="">Select</option>
                {starterPlayers.map((player) => (
                  <option key={player.id} value={player.id}>
                    {player.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <p className="text-sm text-slate-500 mt-2">Starters selected: {starters.length}/{STARTERS_REQUIRED}</p>
        </Card>
      </div>
      <div className="flex justify-end gap-3">
        <Button variant="secondary" onClick={() => router.push("/dashboard")}>Back</Button>
        <Button onClick={handleSave} disabled={starters.length !== STARTERS_REQUIRED || !captain || !vice}>
          Save lineup
        </Button>
      </div>
    </div>
  );
}
