"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Button from "../../../components/Button";
import Form from "../../../components/Form";
import { api } from "../../../lib/api";
import { getToken, setSelectedLeague } from "../../../lib/auth";
import type { League } from "../../../lib/types";

export default function CreateLeaguePage() {
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
    const name = formData.get("name")?.toString() ?? "";
    try {
      const response = await api<League>("/leagues/create", {
        method: "POST",
        body: JSON.stringify({ name }),
      });
      setSelectedLeague(response.league_id);
      router.push("/squad");
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <Form title="Create a League" description="Name your league and invite friends." error={error ?? undefined} onSubmit={handleSubmit}>
      <div>
        <label className="text-sm font-medium text-slate-700" htmlFor="league-name">
          League name
        </label>
        <input id="league-name" name="name" required />
      </div>
      <div className="flex justify-end">
        <Button type="submit">Create</Button>
      </div>
    </Form>
  );
}
