"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Button from "../../../components/Button";
import Card from "../../../components/Card";
import { api } from "../../../lib/api";
import { getToken } from "../../../lib/auth";
import type { Standing } from "../../../lib/types";

type StandingsResponse = {
  standings: Standing[];
};

export default function StandingsPage() {
  const params = useParams<{ leagueId: string }>();
  const router = useRouter();
  const [standings, setStandings] = useState<Standing[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/");
      return;
    }
    const leagueId = Number(params.leagueId);
    if (!leagueId) {
      setError("Invalid league ID");
      return;
    }
    const load = async () => {
      try {
        const data = await api<StandingsResponse>(`/standings/${leagueId}`);
        setStandings(data.standings);
      } catch (err) {
        setError((err as Error).message);
      }
    };
    load();
  }, [params.leagueId, router]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl mb-2">League Standings</h1>
          <p className="text-slate-600">Check how your squad stacks up. Points are placeholders for now.</p>
          {error && <p className="text-red-600 mt-2">{error}</p>}
        </div>
        <Link href="/dashboard">
          <Button variant="secondary">Back to dashboard</Button>
        </Link>
      </div>
      <Card>
        <table className="w-full text-left">
          <thead>
            <tr className="text-slate-500 uppercase text-sm">
              <th className="py-2">Rank</th>
              <th className="py-2">Team</th>
              <th className="py-2 text-right">Points</th>
            </tr>
          </thead>
          <tbody>
            {standings.map((entry, index) => (
              <tr key={entry.team_name} className="border-t border-slate-200">
                <td className="py-3">{index + 1}</td>
                <td className="py-3">{entry.team_name}</td>
                <td className="py-3 text-right">{entry.points}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {standings.length === 0 && <p className="text-slate-600">No standings yet.</p>}
      </Card>
    </div>
  );
}
