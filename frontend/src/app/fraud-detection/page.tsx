"use client";

import { FormEvent, useState } from "react";
import AppShell, { ErrorNotice, PageHeader } from "@/components/AppShell";
import { AlertList, RiskResultCard, inputClass, primaryButtonClass } from "@/components/RiskWidgets";
import { api } from "@/lib/api";
import type { FraudResult } from "@/lib/types";

export default function FraudDetectionPage() {
  const [transactionAmount, setTransactionAmount] = useState(12500);
  const [transactionFrequency, setTransactionFrequency] = useState(18);
  const [internationalTransfer, setInternationalTransfer] = useState(true);
  const [result, setResult] = useState<FraudResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  async function assess(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await api<FraudResult>("/predict-fraud-risk", {
        method: "POST",
        body: JSON.stringify({
          transaction_amount: transactionAmount,
          transaction_frequency: transactionFrequency,
          international_transfer: internationalTransfer,
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
        description="Score a transaction against the fraud scorecard. High-risk results open an alert for review, and every assessment is logged."
      />
      <form onSubmit={assess} className="mt-8 rounded-2xl bg-[#111827] p-5 sm:p-8">
        <h2 className="text-xl font-bold text-yellow-400 sm:text-2xl">Assess a transaction</h2>
        <div className="mt-6 grid grid-cols-1 gap-5 md:grid-cols-3">
          <label className="block text-sm text-slate-300">
            Transaction amount (EUR)
            <input type="number" min="0.01" step="0.01" required value={transactionAmount} onChange={(e) => setTransactionAmount(Number(e.target.value))} className={inputClass} />
          </label>
          <label className="block text-sm text-slate-300">
            Transactions in the period
            <input type="number" min="1" step="1" required value={transactionFrequency} onChange={(e) => setTransactionFrequency(Number(e.target.value))} className={inputClass} />
          </label>
          <label className="block text-sm text-slate-300">
            International transfer
            <select value={internationalTransfer ? "yes" : "no"} onChange={(e) => setInternationalTransfer(e.target.value === "yes")} className={inputClass}>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </label>
        </div>
        <button type="submit" disabled={loading} className={primaryButtonClass}>
          {loading ? "Assessing…" : "Assess fraud risk"}
        </button>
        {error && <ErrorNotice message={error} />}
      </form>
      {result && (
        <RiskResultCard
          level={result.fraud_level}
          score={result.fraud_score}
          recommendation={result.recommendation}
          factors={result.factors}
          assessmentId={result.assessment_id}
          engine={result.engine}
          alertId={result.alert_id}
          alertLabel="Fraud alert"
        />
      )}
      <AlertList kind="fraud" title="Open fraud alerts" refreshKey={refreshKey} />
    </AppShell>
  );
}
