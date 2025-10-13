"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Button from "./Button";
import { clearAuth, getCurrentUser, getToken } from "../lib/auth";

export default function Navbar() {
  const [authenticated, setAuthenticated] = useState(false);
  const [userName, setUserName] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = getToken();
    setAuthenticated(Boolean(token));
    const user = getCurrentUser();
    setUserName(user?.name ?? null);
  }, [pathname]);

  const handleLogout = () => {
    clearAuth();
    setAuthenticated(false);
    router.push("/");
  };

  return (
    <header className="bg-brand text-white">
      <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
        <Link href="/" className="text-xl font-bold">
          GridCap
        </Link>
        <nav className="flex items-center gap-4">
          {authenticated ? (
            <>
              <span className="text-sm text-slate-100">{userName}</span>
              <Link href="/dashboard" className="text-sm hover:underline">
                Dashboard
              </Link>
              <Button variant="secondary" onClick={handleLogout}>
                Log out
              </Button>
            </>
          ) : (
            <Link href="/" className="text-sm hover:underline">
              Sign in
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
