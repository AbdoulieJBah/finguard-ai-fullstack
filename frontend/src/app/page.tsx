"use client";

import { useCallback, useEffect, useState } from "react";
import { Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import AppShell, { ErrorNotice, PageHeader } from "@/components/AppShell";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import type { DashboardMetrics, RiskTrend } from "@/lib/types";

const plural = (count: number, noun: string) => `${count} ${noun}${count === 1 ? "" : "s"}`;

const tooltipStyle = { backgroundColor: "#0F172A", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, color: "#fff" };

function Stat({ label, value, note, colour }: { label: string; value: string | number; note: string; colour: string }) {
  return (
    <div className="rounded-2xl bg-[#111827] p-6">
      <p className="text-slate-400">{label}</p>
      <p className={`mt-3 text-4xl font-bold sm:text-5xl ${colour}`}>{value}</p>
      <p className="mt-2 text-sm text-slate-500">{note}</p>
    </div>
  );
}

function ChartCard({ title, description, colour, children }: { title: string; description: string; colour: string; children: React.ReactElement }) {
  return (
    <div className="rounded-2xl bg-[#111827] p-5 sm:p-8">
      <h2 className={`text-2xl font-bold ${colour}`}>{title}</h2>
      <p className="mt-2 text-slate-400">{description}</p>
      <div className="mt-8 h-72">
        <ResponsiveContainer width="100%" height="100%">
          {children}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [trends, setTrends] = useState<RiskTrend[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setError("");
    Promise.all([api<DashboardMetrics>("/dashboard-metrics"), api<RiskTrend[]>("/risk-trends")])
      .then(([m, t]) => {
        setMetrics(m);
        setTrends(t);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Could not load the dashboard"));
  }, []);

  useEffect(() => {
    if (user) load();
  }, [user, load]);

  return (
    <AppShell>
      <PageHeader
        eyebrow="Banking risk intelligence"
        title="Executive Dashboard"
        description="Live figures from the FinGuard database: open fraud alerts, AML cases and logged risk assessments. Demo data is simulated."
      />
      {error && <ErrorNotice message={error} onRetry={load} />}
      {!metrics && !error && <p className="mt-10 text-slate-400">Loading figures…</p>}
      {metrics && (
        <>
          <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
            <Stat label="Average risk score" value={`${metrics.risk_score}/100`} note={`Across ${metrics.assessments_30d} assessments in the last 30 days`} colour="text-cyan-400" />
            <Stat label="Open fraud alerts" value={metrics.fraud_alerts} note="Not yet closed" colour="text-red-400" />
            <Stat label="Open AML cases" value={metrics.aml_cases} note="Not yet closed" colour="text-yellow-400" />
            <Stat label="Risk assessments" value={metrics.assessments_logged.toLocaleString()} note="Logged with inputs and scores" colour="text-green-400" />
          </div>

          <div className="mt-10 grid grid-cols-1 gap-8 xl:grid-cols-2">
            <ChartCard title="Average Risk Score" description="Mean assessment score per month." colour="text-cyan-400">
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="month" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" allowDecimals={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Line type="monotone" dataKey="risk" name="Average score" stroke="#22D3EE" strokeWidth={3} />
              </LineChart>
            </ChartCard>
            <ChartCard title="Fraud Alerts Opened" description="High-risk fraud assessments per month." colour="text-red-400">
              <AreaChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="month" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" allowDecimals={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Area type="monotone" dataKey="fraud" name="Fraud alerts" stroke="#F87171" fill="#F87171" fillOpacity={0.3} />
              </AreaChart>
            </ChartCard>
          </div>

          <div className="mt-8">
            <ChartCard title="AML Cases Opened" description="High-risk AML screenings per month." colour="text-yellow-400">
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="month" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" allowDecimals={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Line type="monotone" dataKey="aml" name="AML cases" stroke="#FACC15" strokeWidth={3} />
              </LineChart>
            </ChartCard>
          </div>

          <div className="mt-8 rounded-2xl bg-[#111827] p-5 sm:p-8">
            <h2 className="text-2xl font-bold text-orange-300">Summary</h2>
            <p className="mt-4 leading-8 text-slate-300">
              {plural(metrics.fraud_alerts, "fraud alert")} and {plural(metrics.aml_cases, "AML case")} {metrics.fraud_alerts + metrics.aml_cases === 1 ? "is" : "are"}{" "}
              open, {metrics.high_priority_alerts} of them rated High or Critical. The average risk score over the last 30 days is {metrics.risk_score}/100. Review high-priority items first on the Fraud
              Detection and AML Monitoring pages.
            </p>
          </div>
        </>
      )}
    </AppShell>
  );
}
