"use client";

import { FormEvent, useState } from "react";
import AppShell, { ErrorNotice, PageHeader } from "@/components/AppShell";
import { AlertList, RiskResultCard, inputClass, primaryButtonClass } from "@/components/RiskWidgets";
import { api } from "@/lib/api";
import type { AmlResult } from "@/lib/types";

export default function AMLMonitoringPage() {
  const [transactionAmount, setTransactionAmount] = useState(25000);
  const [countryRisk, setCountryRisk] = useState("high");
  const [cashTransaction, setCashTransaction] = useState(false);
  const [politicallyExposed, setPoliticallyExposed] = useState(false);
  const [result, setResult] = useState<AmlResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  async function assess(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await api<AmlResult>("/predict-aml-risk", {
        method: "POST",
        body: JSON.stringify({
          transaction_amount: transactionAmount,
          country_risk: countryRisk,
          cash_transaction: cashTransaction,
          politically_exposed: politicallyExposed,
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
        eyebrow="Anti-money laundering"
        title="AML Monitoring"
        description="Screen a transaction for money-laundering risk. High-risk results open an AML case, and every assessment is logged."
      />
      <form onSubmit={assess} className="mt-8 rounded-2xl bg-[#111827] p-5 sm:p-8">
        <h2 className="text-xl font-bold text-yellow-400 sm:text-2xl">Screen a transaction</h2>
        <div className="mt-6 grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
          <label className="block text-sm text-slate-300">
            Transaction amount (EUR)
            <input type="number" min="0.01" step="0.01" required value={transactionAmount} onChange={(e) => setTransactionAmount(Number(e.target.value))} className={inputClass} />
          </label>
          <label className="block text-sm text-slate-300">
            Country risk
            <select value={countryRisk} onChange={(e) => setCountryRisk(e.target.value)} className={inputClass}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </label>
          <label className="block text-sm text-slate-300">
            Cash transaction
            <select value={cashTransaction ? "yes" : "no"} onChange={(e) => setCashTransaction(e.target.value === "yes")} className={inputClass}>
              <option value="no">No</option>
              <option value="yes">Yes</option>
            </select>
          </label>
          <label className="block text-sm text-slate-300">
            Politically exposed person
            <select value={politicallyExposed ? "yes" : "no"} onChange={(e) => setPoliticallyExposed(e.target.value === "yes")} className={inputClass}>
              <option value="no">No</option>
              <option value="yes">Yes</option>
            </select>
          </label>
        </div>
        <button type="submit" disabled={loading} className={primaryButtonClass}>
          {loading ? "Screening…" : "Assess AML risk"}
        </button>
        {error && <ErrorNotice message={error} />}
      </form>
      {result && (
        <RiskResultCard
          level={result.aml_level}
          score={result.aml_score}
          recommendation={result.recommendation}
          factors={result.factors}
          assessmentId={result.assessment_id}
          engine={result.engine}
          alertId={result.alert_id}
          alertLabel="AML case"
        />
      )}
      <AlertList kind="aml" title="Open AML cases" refreshKey={refreshKey} />
    </AppShell>
  );
}
