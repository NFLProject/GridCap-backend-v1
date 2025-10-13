"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import Button from "../components/Button";
import Card from "../components/Card";
import Form from "../components/Form";
import { api } from "../lib/api";
import { setCurrentUser, setToken } from "../lib/auth";
import type { AuthResponse } from "../lib/types";

export default function HomePage() {
  const router = useRouter();
  const [registerError, setRegisterError] = useState<string | null>(null);
  const [loginError, setLoginError] = useState<string | null>(null);

  const handleRegister = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const payload = {
      name: formData.get("name")?.toString() ?? "",
      email: formData.get("email")?.toString() ?? "",
      password: formData.get("password")?.toString() ?? "",
    };
    try {
      const response = await api<AuthResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setToken(response.token);
      setCurrentUser({ id: response.id, name: response.name, email: response.email });
      router.push("/dashboard");
    } catch (error) {
      setRegisterError((error as Error).message);
    }
  };

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const payload = {
      email: formData.get("email")?.toString() ?? "",
      password: formData.get("password")?.toString() ?? "",
    };
    try {
      const response = await api<AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setToken(response.token);
      setCurrentUser({ id: response.id, name: response.name, email: response.email });
      router.push("/dashboard");
    } catch (error) {
      setLoginError((error as Error).message);
    }
  };

  return (
    <div className="grid gap-8 md:grid-cols-2">
      <Card title="GridCap Fantasy Football">
        <p>
          Draft the ultimate NFL squad, manage your starters, and compete with friends in custom leagues. GridCap
          brings the salary-cap style you love to American football.
        </p>
        <ul className="list-disc list-inside text-slate-700 space-y-2">
          <li>Build a 15-player roster under a $100m salary cap.</li>
          <li>Set your weekly starters and pick captain &amp; vice for bonus points.</li>
          <li>Track league standings and dominate the season.</li>
        </ul>
      </Card>
      <div className="space-y-6">
        <Form title="Create an account" error={registerError ?? undefined} onSubmit={handleRegister}>
          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="register-name">
              Name
            </label>
            <input id="register-name" name="name" type="text" required />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="register-email">
              Email
            </label>
            <input id="register-email" name="email" type="email" required />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="register-password">
              Password
            </label>
            <input id="register-password" name="password" type="password" minLength={6} required />
          </div>
          <div className="flex justify-end">
            <Button type="submit">Sign up</Button>
          </div>
        </Form>
        <Form title="Log in" error={loginError ?? undefined} onSubmit={handleLogin}>
          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="login-email">
              Email
            </label>
            <input id="login-email" name="email" type="email" required />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="login-password">
              Password
            </label>
            <input id="login-password" name="password" type="password" required />
          </div>
          <div className="flex justify-end">
            <Button type="submit">Log in</Button>
          </div>
        </Form>
      </div>
    </div>
  );
}
