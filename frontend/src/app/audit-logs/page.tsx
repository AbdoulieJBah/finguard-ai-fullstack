"use client";

import { useCallback, useEffect, useState } from "react";
import AppShell, { ErrorNotice, PageHeader } from "@/components/AppShell";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import { AUDIT_ROLES, type AuditLogResponse } from "@/lib/types";

const STATUS_STYLES: Record<string, string> = {
  Completed: "bg-emerald-400/10 text-emerald-300",
  Failed: "bg-red-500/10 text-red-300",
  Open: "bg-amber-400/10 text-amber-300",
};

export default function AuditLogsPage() {
  const { user } = useAuth();
  const [data, setData] = useState<AuditLogResponse | null>(null);
  const [error, setError] = useState("");
  const allowed = !!user && AUDIT_ROLES.includes(user.role);

  const load = useCallback(() => {
    setError("");
    api<AuditLogResponse>("/audit-logs?limit=100")
      .then(setData)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Could not load the audit log"));
  }, []);

  useEffect(() => {
    if (allowed) load();
  }, [allowed, load]);

  return (
    <AppShell roles={AUDIT_ROLES}>
      <PageHeader
        eyebrow="Compliance"
        title="Audit Log"
        description="Every sign-in, failed sign-in, payment, assessment and alert, newest first. Visible to Administrators and Compliance Officers."
      />
      {error && <ErrorNotice message={error} onRetry={load} />}
      {data && (
        <>
          <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="rounded-2xl bg-[#111827] p-6">
              <p className="text-slate-400">Audit events</p>
              <p className="mt-3 text-4xl font-bold text-cyan-400">{data.total_events.toLocaleString()}</p>
            </div>
            <div className="rounded-2xl bg-[#111827] p-6">
              <p className="text-slate-400">Risk assessments logged</p>
              <p className="mt-3 text-4xl font-bold text-green-400">{data.assessments_logged.toLocaleString()}</p>
            </div>
            <div className="rounded-2xl bg-[#111827] p-6">
              <p className="text-slate-400">Failed sign-ins (24 hours)</p>
              <p className="mt-3 text-4xl font-bold text-red-400">{data.failed_logins_24h}</p>
            </div>
          </div>
          <section className="mt-8 rounded-2xl bg-[#111827] p-5 sm:p-8">
            <h2 className="text-xl font-bold text-orange-300 sm:text-2xl">Recent activity</h2>
            {data.items.length === 0 ? (
              <p className="mt-4 text-slate-400">No events yet.</p>
            ) : (
              <ul className="mt-6 space-y-3">
                {data.items.map((item) => (
                  <li key={item.id} className="flex flex-col justify-between gap-3 rounded-xl bg-[#1F2937] p-4 md:flex-row md:items-center">
                    <div className="min-w-0">
                      <p className="font-semibold">{item.action}</p>
                      <p className="mt-1 text-sm text-slate-400">By {item.user}</p>
                    </div>
                    <div className="flex shrink-0 items-center gap-3 text-sm">
                      <time dateTime={item.time} className="text-slate-400">
                        {new Date(item.time).toLocaleString()}
                      </time>
                      <span className={`rounded-full px-3 py-1 font-semibold ${STATUS_STYLES[item.status] ?? "bg-white/5 text-slate-300"}`}>{item.status}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
      {!data && !error && allowed && <p className="mt-8 text-slate-400">Loading…</p>}
    </AppShell>
  );
}
