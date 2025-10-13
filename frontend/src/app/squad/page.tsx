"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import Button from "../../components/Button";
import Card from "../../components/Card";
import { api } from "../../lib/api";
import { getSelectedLeague, getToken } from "../../lib/auth";
import type { Player, Squad, SquadSaveResponse } from "../../lib/types";

const SALARY_CAP = 100;
const SQUAD_SIZE = 15;

export default function SquadPage() {
  const router = useRouter();
  const [players, setPlayers] = useState<Player[]>([]);
  const [selectedPlayers, setSelectedPlayers] = useState<Player[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
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
        const [playerList, squad] = await Promise.all([
          api<Player[]>("/players"),
          api<SquadSaveResponse>(`/squad?league_id=${leagueId}`),
        ]);
        setPlayers(playerList);
        if (squad && squad.players) {
          setSelectedPlayers(squad.players);
        }
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [leagueId, router]);

  const totalCost = useMemo(() => selectedPlayers.reduce((sum, p) => sum + p.cost, 0), [selectedPlayers]);

  const togglePlayer = (player: Player) => {
    setError(null);
    setSuccess(null);
    setSelectedPlayers((prev) => {
      const exists = prev.some((p) => p.id === player.id);
      if (exists) {
        return prev.filter((p) => p.id !== player.id);
      }
      if (prev.length >= SQUAD_SIZE) {
        setError(`You can only select ${SQUAD_SIZE} players.`);
        return prev;
      }
      return [...prev, player];
    });
  };

  const handleSave = async () => {
    if (!leagueId) return;
    if (selectedPlayers.length !== SQUAD_SIZE) {
      setError(`Select exactly ${SQUAD_SIZE} players.`);
      return;
    }
    try {
      setError(null);
      const response = await api<Squad>("/squad/save", {
        method: "POST",
        body: JSON.stringify({ league_id: leagueId, player_ids: selectedPlayers.map((p) => p.id) }),
      });
      setSuccess("Squad saved! Proceed to set your lineup.");
      setSelectedPlayers(response.players);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const grouped = useMemo(() => {
    return players.reduce<Record<string, Player[]>>((acc, player) => {
      acc[player.position] = acc[player.position] || [];
      acc[player.position].push(player);
      return acc;
    }, {});
  }, [players]);

  if (loading) {
    return <p>Loading...</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl mb-2">Build your squad</h1>
        <p className="text-slate-600">Select {SQUAD_SIZE} players under the ${SALARY_CAP}m cap.</p>
        <p className={`mt-2 font-medium ${totalCost > SALARY_CAP ? "text-red-600" : "text-green-600"}`}>
          Budget used: ${totalCost.toFixed(1)}m / ${SALARY_CAP}m
        </p>
        {error && <p className="text-red-600 mt-2">{error}</p>}
        {success && <p className="text-green-600 mt-2">{success}</p>}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {Object.entries(grouped).map(([position, positionPlayers]) => (
          <Card key={position} title={`${position} (${positionPlayers.length})`}>
            <ul className="space-y-2 max-h-80 overflow-y-auto pr-2">
              {positionPlayers.map((player) => {
                const selected = selectedPlayers.some((p) => p.id === player.id);
                return (
                  <li key={player.id}>
                    <button
                      type="button"
                      onClick={() => togglePlayer(player)}
                      className={`w-full flex justify-between items-center px-3 py-2 rounded border ${
                        selected ? "border-brand bg-sky-50" : "border-slate-200"
                      }`}
                    >
                      <span>
                        {player.name} <span className="text-xs text-slate-500">{player.team}</span>
                      </span>
                      <span className="font-semibold">${player.cost.toFixed(1)}m</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </Card>
        ))}
      </div>
      <div className="flex justify-between items-center">
        <p>
          Selected: {selectedPlayers.length}/{SQUAD_SIZE}
        </p>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={() => router.push("/dashboard")}>Cancel</Button>
          <Button onClick={handleSave} disabled={selectedPlayers.length !== SQUAD_SIZE || totalCost > SALARY_CAP}>
            Save squad
          </Button>
          <Button
            onClick={() => router.push("/lineup")}
            variant="secondary"
            disabled={selectedPlayers.length !== SQUAD_SIZE || totalCost > SALARY_CAP}
          >
            Set lineup
          </Button>
        </div>
      </div>
    </div>
  );
}
