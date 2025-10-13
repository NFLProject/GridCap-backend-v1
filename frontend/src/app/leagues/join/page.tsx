"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Button from "../../../components/Button";
import Form from "../../../components/Form";
import { api } from "../../../lib/api";
import { getToken, setSelectedLeague } from "../../../lib/auth";
import type { League } from "../../../lib/types";

export default function JoinLeaguePage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/");
    }
  }, [router]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const leagueId = Number(formData.get("league_id"));
    try {
      await api("/leagues/join", {
        method: "POST",
        body: JSON.stringify({ league_id: leagueId }),
      });
      setSelectedLeague(leagueId);
      router.push("/squad");
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <Form title="Join a League" description="Enter a league ID shared with you." error={error ?? undefined} onSubmit={handleSubmit}>
      <div>
        <label className="text-sm font-medium text-slate-700" htmlFor="league-id">
          League ID
        </label>
        <input id="league-id" name="league_id" type="number" min={1} required />
      </div>
      <div className="flex justify-end">
        <Button type="submit">Join</Button>
      </div>
    </Form>
  );
}
