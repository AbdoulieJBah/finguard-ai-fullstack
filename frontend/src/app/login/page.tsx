"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Landmark, LockKeyhole } from "lucide-react";
import { useAuth } from "@/components/AuthProvider";

const DEMO_USERS = [
  { email: "demo@finguard.ai", role: "Administrator" },
  { email: "analyst@finguard.ai", role: "Risk Analyst" },
  { email: "compliance@finguard.ai", role: "Compliance Officer" },
];

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("demo@finguard.ai");
  const [password, setPassword] = useState("FinGuard123!");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email, password);
      router.push("/");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign in failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-[#080e1a] p-4 text-white sm:p-6">
      <div className="w-full max-w-md rounded-3xl border border-white/10 bg-[#111827] p-6 shadow-2xl sm:p-8">
        <div className="mb-8 flex items-center gap-3">
          <span className="grid h-12 w-12 place-items-center rounded-2xl bg-cyan-400 text-slate-950">
            <Landmark />
          </span>
          <div>
            <h1 className="text-2xl font-bold">FinGuard</h1>
            <p className="text-sm text-slate-400">Secure banking workspace</p>
          </div>
        </div>
        <form onSubmit={submit} className="space-y-5">
          <label className="block text-sm text-slate-300">
            Email
            <input className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950/60 p-3 outline-none focus:border-cyan-400" value={email} onChange={(e) => setEmail(e.target.value)} type="email" autoComplete="username" required />
          </label>
          <label className="block text-sm text-slate-300">
            Password
            <input className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950/60 p-3 outline-none focus:border-cyan-400" value={password} onChange={(e) => setPassword(e.target.value)} type="password" autoComplete="current-password" required />
          </label>
          {error && <p className="rounded-lg bg-red-500/10 p-3 text-sm text-red-300">{error}</p>}
          <button disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-400 p-3 font-bold text-slate-950 disabled:opacity-50">
            <LockKeyhole size={18} />
            {loading ? "Verifying…" : "Sign in securely"}
          </button>
        </form>
        <div className="mt-6 rounded-xl bg-white/5 p-4 text-xs leading-5 text-slate-400">
          <p className="font-semibold text-slate-300">Demo users (password FinGuard123!)</p>
          <ul className="mt-2 space-y-1">
            {DEMO_USERS.map((demo) => (
              <li key={demo.email}>
                <button type="button" onClick={() => setEmail(demo.email)} className="text-left hover:text-cyan-300">
                  {demo.email} · {demo.role}
                </button>
              </li>
            ))}
          </ul>
          <p className="mt-3">All data is simulated. Do not use this application to process real funds.</p>
        </div>
      </div>
    </main>
  );
}
