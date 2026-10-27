"use client";

import { useCallback, useEffect, useState } from "react";
import AppShell, { ErrorNotice, PageHeader } from "@/components/AppShell";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import type { SystemHealth } from "@/lib/types";

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function Card({ label, value, note, colour }: { label: string; value: string; note: string; colour: string }) {
  return (
    <div className="rounded-2xl bg-[#111827] p-6">
      <p className="text-slate-400">{label}</p>
      <p className={`mt-3 text-3xl font-bold ${colour}`}>{value}</p>
      <p className="mt-3 text-sm text-slate-500">{note}</p>
    </div>
  );
}

export default function SystemHealthPage() {
  const { user } = useAuth();
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setError("");
    api<SystemHealth>("/system-health")
      .then(setHealth)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Could not reach the API"));
  }, []);

  useEffect(() => {
    if (user) load();
  }, [user, load]);

  return (
    <AppShell>
      <PageHeader
        eyebrow="Infrastructure"
        title="System Health"
        description="Measured on each check: API status, database round-trip time and uptime."
      />
      {error && <ErrorNotice message={error} onRetry={load} />}
      {!health && !error && <p className="mt-8 text-slate-400">Checking…</p>}
      {health && (
        <>
          <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
            <Card label="Backend API" value={health.backend} note={`FastAPI · version ${health.version}`} colour="text-green-400" />
            <Card
              label="Database"
              value={health.database}
              note={`${health.database_engine}${health.database_latency_ms !== null ? ` · ${health.database_latency_ms} ms round trip` : ""}`}
              colour={health.database === "Connected" ? "text-green-400" : "text-red-400"}
            />
            <Card
              label="Storage"
              value={health.persistent_storage ? "Persistent" : "Temporary"}
              note={health.persistent_storage ? "Data survives redeploys" : "Local SQLite file: data is reset on redeploy"}
              colour={health.persistent_storage ? "text-green-400" : "text-amber-300"}
            />
            <Card label="Risk engines" value="Model + rules" note={health.risk_engine} colour="text-cyan-400" />
            <Card label="Copilot" value={health.copilot} note="Keyword routing over live figures" colour="text-purple-400" />
            <Card label="Uptime" value={formatUptime(health.uptime_seconds)} note={`Checked ${new Date(health.checked_at).toLocaleTimeString()}`} colour="text-slate-200" />
          </div>
          <button type="button" onClick={load} className="mt-8 rounded-xl border border-white/10 px-5 py-2.5 text-sm font-semibold hover:bg-white/5">
            Check again
          </button>
        </>
      )}
    </AppShell>
  );
}
