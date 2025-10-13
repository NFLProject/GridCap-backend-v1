"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Button from "../../components/Button";
import Card from "../../components/Card";
import { api } from "../../lib/api";
import { getSelectedLeague, getToken, setSelectedLeague } from "../../lib/auth";
import type { League, MeResponse } from "../../lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<MeResponse | null>(null);
  const [leagues, setLeagues] = useState<League[]>([]);
  const [selectedLeague, setLeagueState] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/");
      return;
    }
    const load = async () => {
      try {
        const me = await api<MeResponse>("/auth/me");
        setUser(me);
        const myLeagues = await api<League[]>("/leagues/mine");
        setLeagues(myLeagues);
        const stored = getSelectedLeague();
        if (stored) {
          setLeagueState(stored);
        }
      } catch (err) {
        setError((err as Error).message);
      }
    };
    load();
  }, [router]);

  const handleSelect = (leagueId: number) => {
    setLeagueState(leagueId);
    setSelectedLeague(leagueId);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl mb-2">Welcome, {user?.name ?? "Coach"}</h1>
        <p className="text-slate-600">Manage your leagues, build squads, and set your winning lineup.</p>
        {error && <p className="text-red-600 mt-2">{error}</p>}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card title="Your Leagues">
          {leagues.length === 0 ? (
            <p className="text-slate-600">Join or create a league to get started.</p>
          ) : (
            <ul className="space-y-2">
              {leagues.map((league) => (
                <li key={league.league_id}>
                  <button
                    type="button"
                    className={`w-full text-left px-4 py-2 rounded border ${
                      selectedLeague === league.league_id ? "border-brand bg-sky-50" : "border-slate-200"
                    }`}
                    onClick={() => handleSelect(league.league_id)}
                  >
                    {league.name}
                  </button>
                </li>
              ))}
            </ul>
          )}
          <div className="flex gap-3 mt-4">
            <Link href="/leagues/create">
              <Button>Create League</Button>
            </Link>
            <Link href="/leagues/join">
              <Button variant="secondary">Join League</Button>
            </Link>
          </div>
        </Card>
        <Card title="Next Steps">
          <div className="space-y-3">
            <Link href="/squad">
              <Button className="w-full" disabled={!selectedLeague}>
                Build Squad
              </Button>
            </Link>
            <Link href="/lineup">
              <Button className="w-full" disabled={!selectedLeague}>
                Set Lineup
              </Button>
            </Link>
            {selectedLeague && (
              <Link href={`/standings/${selectedLeague}`}>
                <Button className="w-full" variant="secondary">
                  View Standings
                </Button>
              </Link>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
