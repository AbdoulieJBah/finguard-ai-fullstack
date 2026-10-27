"use client";

import { FormEvent, useEffect, useState } from "react";
import AppShell, { ErrorNotice, PageHeader } from "@/components/AppShell";
import { useAuth } from "@/components/AuthProvider";
import { AlertList, inputClass, primaryButtonClass } from "@/components/RiskWidgets";
import { api } from "@/lib/api";
import type { FraudContribution, FraudModelCard, FraudModelResult } from "@/lib/types";

const MODEL_CARD_URL = "https://github.com/AbdoulieJBah/finguard-ai-fullstack/blob/main/ml/MODEL_CARD.md";
const LEVEL_COLOURS: Record<string, string> = { Low: "text-emerald-300", Medium: "text-amber-300", High: "text-red-400" };
const pct = (value: number) => (value < 0.001 ? "<0.1%" : `${(value * 100).toFixed(value < 0.1 ? 1 : 0)}%`);

function Explanation({ contributions }: { contributions: FraudContribution[] }) {
  const largest = Math.max(...contributions.map((c) => Math.abs(c.contribution)), 0.01);
  return (
    <ul className="mt-3 space-y-3">
      {contributions.map((c) => {
        const width = `${Math.max(2, (Math.abs(c.contribution) / largest) * 100) / 2}%`;
        const raises = c.contribution > 0;
        return (
          <li key={c.feature}>
            <div className="flex flex-wrap items-baseline justify-between gap-x-3 text-sm">
              <span>
                <span className="text-slate-200">{c.label}</span>
                <span className="text-slate-400"> · {c.value}</span>
              </span>
              <span className={raises ? "text-red-300" : "text-emerald-300"}>
                {raises ? "raises risk" : "lowers risk"} ({c.contribution > 0 ? "+" : ""}
                {c.contribution.toFixed(2)})
              </span>
            </div>
            <div className="relative mt-1 h-2 rounded-full bg-white/5">
              <div className="absolute inset-y-0 left-1/2 w-px bg-white/20" />
              <div
                className={`absolute inset-y-0 rounded-full ${raises ? "left-1/2 bg-red-400" : "right-1/2 bg-emerald-400"}`}
                style={{ width }}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function ModelPanel({ card }: { card: FraudModelCard }) {
  const test = card.metrics.test;
  return (
    <aside className="mt-8 rounded-2xl border border-cyan-400/20 bg-cyan-400/5 p-5 text-sm sm:p-6">
      <h2 className="text-lg font-semibold">About the model</h2>
      <p className="mt-2 leading-6 text-slate-300">
        A logistic scorecard trained on {card.data.rows.toLocaleString()} PaySim transactions ({card.data.frauds.toLocaleString()} frauds), validated
        on later transactions than it was trained on. Version {card.version}, trained {card.trained_at.slice(0, 10)}.
      </p>
      <dl className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div>
          <dt className="text-slate-400">PR-AUC (test)</dt>
          <dd className="text-xl font-bold text-cyan-300">{test.pr_auc.toFixed(3)}</dd>
        </div>
        <div>
          <dt className="text-slate-400">Precision at High</dt>
          <dd className="text-xl font-bold text-cyan-300">{pct(test.at_high.precision)}</dd>
        </div>
        <div>
          <dt className="text-slate-400">Recall at High</dt>
          <dd className="text-xl font-bold text-cyan-300">{pct(test.at_high.recall)}</dd>
        </div>
        <div>
          <dt className="text-slate-400">Alerts per 10,000</dt>
          <dd className="text-xl font-bold text-cyan-300">{test.at_high.alerts_per_10k.toFixed(0)}</dd>
        </div>
      </dl>
      <p className="mt-4 leading-6 text-amber-200/90">
        These scores are high because PaySim fraud follows one simple pattern (an account emptied to the cent); a one-line rule matches the
        model at the High level. Real-world performance would be much lower.
      </p>
      <a href={MODEL_CARD_URL} target="_blank" rel="noreferrer" className="mt-3 inline-block font-semibold text-cyan-300 hover:underline">
        Read the full model card
      </a>
    </aside>
  );
}

export default function FraudDetectionPage() {
  const { user } = useAuth();
  const [amount, setAmount] = useState(180000);
  const [senderBalance, setSenderBalance] = useState(180000);
  const [transactionType, setTransactionType] = useState("TRANSFER");
  const [hour, setHour] = useState("now");
  const [result, setResult] = useState<FraudModelResult | null>(null);
  const [card, setCard] = useState<FraudModelCard | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!user) return;
    api<FraudModelCard>("/models/fraud")
      .then(setCard)
      .catch(() => setCard(null));
  }, [user]);

  async function assess(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await api<FraudModelResult>("/predict-fraud-model", {
        method: "POST",
        body: JSON.stringify({
          amount,
          sender_balance: senderBalance,
          transaction_type: transactionType,
          ...(hour === "now" ? {} : { hour: Number(hour) }),
        }),
      });
      setResult(data);
      setRefreshKey((key) => key + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Assessment failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Fraud monitoring"
        title="Fraud Detection"
        description="Every payment in FinGuard is scored by a fraud model trained on 2.8 million transactions. Try a payment here to see its score and exactly why."
      />
      <form onSubmit={assess} className="mt-8 rounded-2xl bg-[#111827] p-5 sm:p-8">
        <h2 className="text-xl font-bold text-yellow-400 sm:text-2xl">Score a payment</h2>
        <div className="mt-6 grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
          <label className="block text-sm text-slate-300">
            Amount (EUR)
            <input type="number" min="0.01" step="0.01" required value={amount} onChange={(e) => setAmount(Number(e.target.value))} className={inputClass} />
          </label>
          <label className="block text-sm text-slate-300">
            Sender balance before (EUR)
            <input type="number" min="0" step="0.01" required value={senderBalance} onChange={(e) => setSenderBalance(Number(e.target.value))} className={inputClass} />
          </label>
          <label className="block text-sm text-slate-300">
            Type
            <select value={transactionType} onChange={(e) => setTransactionType(e.target.value)} className={inputClass}>
              <option value="TRANSFER">Transfer</option>
              <option value="CASH_OUT">Cash out</option>
            </select>
          </label>
          <label className="block text-sm text-slate-300">
            Time (UTC)
            <select value={hour} onChange={(e) => setHour(e.target.value)} className={inputClass}>
              <option value="now">Now</option>
              {Array.from({ length: 24 }, (_, h) => (
                <option key={h} value={String(h)}>
                  {String(h).padStart(2, "0")}:00
                </option>
              ))}
            </select>
          </label>
        </div>
        <button type="submit" disabled={loading} className={primaryButtonClass}>
          {loading ? "Scoring…" : "Score payment"}
        </button>
        {error && <ErrorNotice message={error} />}
      </form>

      {result && (
        <section className="mt-8 rounded-2xl border border-white/10 bg-[#0F172A] p-5 sm:p-8" aria-live="polite">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
            <div>
              <p className="text-sm text-slate-400">Risk level</p>
              <p className={`mt-1 text-4xl font-bold sm:text-5xl ${LEVEL_COLOURS[result.level] ?? "text-white"}`}>{result.level}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">Fraud probability</p>
              <p className="mt-1 text-4xl font-bold text-cyan-300 sm:text-5xl">{pct(result.probability)}</p>
            </div>
            <div className="text-sm text-slate-400">
              <p>
                High from {pct(result.thresholds.high)} (opens an alert), Medium from {pct(result.thresholds.medium)} (monitored).
              </p>
              <p className="mt-2">Scored at {String(result.hour).padStart(2, "0")}:00 UTC.</p>
            </div>
          </div>
          <h3 className="mt-8 font-semibold">Why: each feature compared with an average payment</h3>
          <Explanation contributions={result.contributions} />
          {result.alert_id ? (
            <p className="mt-6 rounded-xl bg-red-500/10 p-3 text-sm text-red-200">Fraud alert #{result.alert_id} opened for review.</p>
          ) : null}
          <p className="mt-6 text-xs text-slate-500">
            Assessment #{result.assessment_id} logged · fraud scorecard {result.model_version}
          </p>
        </section>
      )}

      {card && <ModelPanel card={card} />}
      <AlertList kind="fraud" title="Open fraud alerts" refreshKey={refreshKey} />
    </AppShell>
  );
}
