"use client";

import { FormEvent, useEffect, useState } from "react";
import { CheckCircle2, ShieldCheck } from "lucide-react";
import AppShell, { ErrorNotice, PageHeader } from "@/components/AppShell";
import { useAuth } from "@/components/AuthProvider";
import { inputClass } from "@/components/RiskWidgets";
import { ApiError, api, newIdempotencyKey } from "@/lib/api";
import type { Account, TransferResult } from "@/lib/types";

export default function TransfersPage() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [from, setFrom] = useState(0);
  const [to, setTo] = useState("FG10000002");
  const [amount, setAmount] = useState(250);
  const [description, setDescription] = useState("Treasury allocation");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<TransferResult | null>(null);
  // One key per payment: kept when a request fails in transit so a retry cannot pay twice,
  // replaced when the payment succeeds or the form changes.
  const [paymentKey, setPaymentKey] = useState(newIdempotencyKey);

  useEffect(() => {
    if (!user) return;
    api<Account[]>("/accounts")
      .then((a) => {
        setAccounts(a);
        if (a[0]) setFrom(a[0].id);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Could not load accounts"));
  }, [user]);

  function edited<T>(setter: (value: T) => void) {
    return (value: T) => {
      setter(value);
      setPaymentKey(newIdempotencyKey());
    };
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const data = await api<TransferResult>("/transfers", {
        method: "POST",
        headers: { "Idempotency-Key": paymentKey },
        body: JSON.stringify({ from_account_id: from, to_account_number: to, amount, description }),
      });
      setResult(data);
      setPaymentKey(newIdempotencyKey());
      setAccounts((current) => current.map((a) => (a.id === from ? { ...a, balance: data.available_balance } : a)));
    } catch (e) {
      if (e instanceof ApiError && e.status === 0) {
        setError(`${e.message} Sending again is safe: this payment will not be made twice.`);
      } else {
        setError(e instanceof Error ? e.message : "Transfer failed");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <PageHeader eyebrow="Payments" title="Internal transfer" description="Move funds between FinGuard accounts with an atomic ledger update." />
      <div className="mt-8 grid gap-6 xl:grid-cols-[minmax(0,680px)_1fr]">
        <form onSubmit={submit} className="space-y-5 rounded-2xl border border-white/10 bg-[#101827] p-6">
          <label className="block text-sm text-slate-300">
            From account
            <select value={from} onChange={(e) => edited(setFrom)(Number(e.target.value))} className={inputClass}>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} · {a.currency} {a.balance.toLocaleString()}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm text-slate-300">
            Recipient account number
            <input value={to} onChange={(e) => edited(setTo)(e.target.value)} className={inputClass} required />
          </label>
          <div className="grid gap-5 sm:grid-cols-2">
            <label className="block text-sm text-slate-300">
              Amount (EUR)
              <input type="number" min="0.01" step="0.01" value={amount} onChange={(e) => edited(setAmount)(Number(e.target.value))} className={inputClass} required />
            </label>
            <label className="block text-sm text-slate-300">
              Payment reference
              <input value={description} onChange={(e) => edited(setDescription)(e.target.value)} className={inputClass} required />
            </label>
          </div>
          {error && <ErrorNotice message={error} />}
          {result && (
            <div className="flex gap-3 rounded-xl bg-emerald-400/10 p-4 text-emerald-200">
              <CheckCircle2 />
              <div>
                <p className="font-semibold">Payment completed</p>
                <p className="text-sm">
                  Reference {result.reference} · Balance €{result.available_balance.toLocaleString()}
                </p>
              </div>
            </div>
          )}
          <button disabled={busy || !accounts.length} className="w-full rounded-xl bg-cyan-400 p-3 font-bold text-slate-950 disabled:opacity-50">
            {busy ? "Authorising…" : "Review and send"}
          </button>
          {user && accounts.length === 0 && !error && <p className="text-sm text-slate-400">There are no accounts linked to your user.</p>}
        </form>
        <aside className="h-fit rounded-2xl border border-cyan-400/20 bg-cyan-400/5 p-6">
          <ShieldCheck className="text-cyan-300" />
          <h2 className="mt-4 font-semibold">Protected transfer</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            Balances update in one database transaction. Failed validation or insufficient funds roll back the entire payment. Each payment carries
            an idempotency key, so a retried request after a network error is never paid twice.
          </p>
          <p className="mt-5 text-xs text-amber-300">Demo environment: no real money is moved.</p>
        </aside>
      </div>
    </AppShell>
  );
}
