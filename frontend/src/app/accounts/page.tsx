"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowDownLeft, ArrowUpRight, Send } from "lucide-react";
import AppShell, { ErrorNotice, PageHeader } from "@/components/AppShell";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import type { Account, Transaction } from "@/lib/types";

const fmt = (amount: number, currency = "EUR") => new Intl.NumberFormat("en-GB", { style: "currency", currency }).format(amount);

export default function AccountsPage() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState<Account[] | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setError("");
    Promise.all([api<Account[]>("/accounts"), api<Transaction[]>("/transactions")])
      .then(([a, t]) => {
        setAccounts(a);
        setTransactions(t);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Could not load accounts"));
  }, []);

  useEffect(() => {
    if (user) load();
  }, [user, load]);

  return (
    <AppShell>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <PageHeader eyebrow="Treasury workspace" title="Accounts" description="Available cash and settled ledger activity." />
        <Link href="/transfers" className="flex items-center gap-2 rounded-xl bg-cyan-400 px-5 py-3 font-bold text-slate-950">
          <Send size={18} />
          New payment
        </Link>
      </div>
      {error && <ErrorNotice message={error} onRetry={load} />}
      {accounts !== null && accounts.length === 0 && (
        <p className="mt-8 rounded-2xl bg-[#111827] p-6 text-slate-400">There are no accounts linked to your user.</p>
      )}
      <section className="mt-8 grid gap-5 lg:grid-cols-2">
        {(accounts ?? []).map((a) => (
          <article key={a.id} className="relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-slate-800 to-slate-900 p-6">
            <div className="absolute -right-12 -top-12 h-40 w-40 rounded-full bg-cyan-400/10" />
            <div className="flex justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm text-slate-400">
                  {a.type} · •••• {a.account_number.slice(-4)}
                </p>
                <h2 className="mt-1 text-lg font-semibold">{a.name}</h2>
              </div>
              <span className="h-fit rounded-full bg-emerald-400/10 px-3 py-1 text-xs text-emerald-300">{a.status}</span>
            </div>
            <p className="mt-10 text-sm text-slate-400">Available balance</p>
            <p className="mt-1 text-3xl font-bold">{fmt(a.balance, a.currency)}</p>
          </article>
        ))}
      </section>
      {transactions.length > 0 && (
        <section className="mt-8 overflow-hidden rounded-2xl border border-white/10 bg-[#101827]">
          <div className="border-b border-white/10 p-5">
            <h2 className="text-lg font-semibold">Recent transactions</h2>
          </div>
          <div className="divide-y divide-white/5">
            {transactions.map((t) => (
              <div key={t.id} className="flex items-center gap-4 p-4 sm:p-5">
                <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${t.direction === "credit" ? "bg-emerald-400/10 text-emerald-300" : "bg-slate-700 text-slate-300"}`}>
                  {t.direction === "credit" ? <ArrowDownLeft /> : <ArrowUpRight />}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">{t.counterparty}</p>
                  <p className="truncate text-xs text-slate-500">
                    {t.description} · {new Date(t.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className={t.amount > 0 ? "font-semibold text-emerald-300" : "font-semibold"}>
                    {t.amount > 0 ? "+" : ""}
                    {fmt(t.amount)}
                  </p>
                  <p className="text-xs text-slate-500">{t.status}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </AppShell>
  );
}
