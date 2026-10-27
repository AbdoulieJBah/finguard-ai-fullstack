"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Alert } from "@/lib/types";

const LEVEL_COLOURS: Record<string, string> = {
  Low: "text-emerald-300",
  Medium: "text-amber-300",
  High: "text-red-400",
  Critical: "text-red-500",
};

export function RiskResultCard(props: {
  level: string;
  score: number;
  recommendation: string;
  factors: string[];
  assessmentId: number;
  engine: string;
  alertId?: number | null;
  alertLabel?: string;
  extra?: React.ReactNode;
}) {
  return (
    <section className="mt-8 rounded-2xl border border-white/10 bg-[#0F172A] p-5 sm:p-8" aria-live="polite">
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div>
          <p className="text-sm text-slate-400">Risk level</p>
          <p className={`mt-1 text-4xl font-bold sm:text-5xl ${LEVEL_COLOURS[props.level] ?? "text-white"}`}>{props.level}</p>
        </div>
        <div>
          <p className="text-sm text-slate-400">Score</p>
          <p className="mt-1 text-4xl font-bold text-cyan-300 sm:text-5xl">{props.score}</p>
        </div>
      </div>
      {props.extra}
      <div className="mt-6">
        <p className="text-sm text-slate-400">Why</p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-200">
          {props.factors.map((factor) => (
            <li key={factor}>{factor}</li>
          ))}
        </ul>
      </div>
      <div className="mt-6">
        <p className="text-sm text-slate-400">Recommendation</p>
        <p className="mt-1 text-lg">{props.recommendation}</p>
      </div>
      {props.alertId ? (
        <p className="mt-6 rounded-xl bg-red-500/10 p-3 text-sm text-red-200">
          {props.alertLabel ?? "Alert"} #{props.alertId} opened for review.
        </p>
      ) : null}
      <p className="mt-6 text-xs text-slate-500">
        Assessment #{props.assessmentId} logged · {props.engine} (rule-based scorecard)
      </p>
    </section>
  );
}

const money = new Intl.NumberFormat("en-GB", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });

/** Open alerts of one kind, newest first. Pass a changing `refreshKey` to reload after a new assessment. */
export function AlertList({ kind, title, refreshKey }: { kind: "fraud" | "aml"; title: string; refreshKey: number }) {
  const [alerts, setAlerts] = useState<Alert[] | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setError("");
    api<Alert[]>(`/alerts?kind=${kind}&limit=8`)
      .then(setAlerts)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Could not load alerts"));
  }, [kind]);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  return (
    <section className="mt-8 rounded-2xl bg-[#111827] p-5 sm:p-8">
      <h2 className="text-xl font-bold sm:text-2xl">{title}</h2>
      {error && <p className="mt-4 text-sm text-red-300">{error}</p>}
      {alerts === null && !error && <p className="mt-4 text-sm text-slate-400">Loading…</p>}
      {alerts !== null && alerts.length === 0 && <p className="mt-4 text-sm text-slate-400">No open items.</p>}
      {alerts !== null && alerts.length > 0 && (
        <ul className="mt-4 divide-y divide-white/5">
          {alerts.map((alert) => (
            <li key={alert.id} className="flex flex-col gap-2 py-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <p className="font-semibold">
                  #{alert.id} · {alert.subject}
                </p>
                <p className="mt-1 text-sm text-slate-400">{alert.reason}</p>
                <p className="mt-1 text-xs text-slate-500">{new Date(alert.created_at).toLocaleString()}</p>
              </div>
              <div className="flex shrink-0 items-center gap-2 text-sm">
                {alert.amount !== null && <span className="text-slate-300">{money.format(alert.amount)}</span>}
                <span className={`rounded-full bg-white/5 px-3 py-1 font-semibold ${LEVEL_COLOURS[alert.level] ?? ""}`}>{alert.level}</span>
                <span className="rounded-full bg-white/5 px-3 py-1 text-slate-300">{alert.status}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export const inputClass = "mt-2 w-full rounded-xl border border-white/10 bg-[#1F2937] p-3 text-white outline-none focus:border-cyan-400";
export const primaryButtonClass =
  "mt-6 w-full rounded-xl bg-cyan-400 px-8 py-3 font-bold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-50 sm:w-auto";
