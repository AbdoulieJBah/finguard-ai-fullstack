"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";

export type User = { id: number; name: string; email: string; role: string };
type AuthValue = { user: User | null; ready: boolean; login: (email: string, password: string) => Promise<void>; logout: () => void };
const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!localStorage.getItem("finguard_token")) { setReady(true); return; }
    api<User>("/me").then(setUser).catch(() => localStorage.removeItem("finguard_token")).finally(() => setReady(true));
  }, []);
  async function login(email: string, password: string) {
    const data = await api<{ access_token: string; user: User }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
    localStorage.setItem("finguard_token", data.access_token); setUser(data.user);
  }
  function logout() { localStorage.removeItem("finguard_token"); setUser(null); window.location.href = "/login"; }
  return <AuthContext.Provider value={{ user, ready, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
