"use client";

import { FormEvent, useState } from "react";
import AppShell, { ErrorNotice, PageHeader } from "@/components/AppShell";
import { RiskResultCard, inputClass, primaryButtonClass } from "@/components/RiskWidgets";
import { api } from "@/lib/api";
import type { CreditResult } from "@/lib/types";

export default function CreditRiskPage() {
  const [income, setIncome] = useState(50000);
  const [loanAmount, setLoanAmount] = useState(20000);
  const [creditScore, setCreditScore] = useState(720);
  const [result, setResult] = useState<CreditResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function assess(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await api<CreditResult>("/predict-credit-risk", {
        method: "POST",
        body: JSON.stringify({ income, loan_amount: loanAmount, credit_score: creditScore }),
      });
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Assessment failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Lending"
        title="Credit Risk"
        description="Score a loan application on credit score and affordability. Every assessment is logged with its inputs."
      />
      <form onSubmit={assess} className="mt-8 rounded-2xl bg-[#111827] p-5 sm:p-8">
        <h2 className="text-xl font-bold text-yellow-400 sm:text-2xl">Assess an application</h2>
        <div className="mt-6 grid grid-cols-1 gap-5 md:grid-cols-3">
          <label className="block text-sm text-slate-300">
            Annual income (EUR)
            <input type="number" min="1" step="1" required value={income} onChange={(e) => setIncome(Number(e.target.value))} className={inputClass} />
          </label>
          <label className="block text-sm text-slate-300">
            Loan amount (EUR)
            <input type="number" min="1" step="1" required value={loanAmount} onChange={(e) => setLoanAmount(Number(e.target.value))} className={inputClass} />
          </label>
          <label className="block text-sm text-slate-300">
            Credit score (300-850)
            <input type="number" min="300" max="850" step="1" required value={creditScore} onChange={(e) => setCreditScore(Number(e.target.value))} className={inputClass} />
          </label>
        </div>
        <button type="submit" disabled={loading} className={primaryButtonClass}>
          {loading ? "Assessing…" : "Assess credit risk"}
        </button>
        {error && <ErrorNotice message={error} />}
      </form>
      {result && (
        <RiskResultCard
          level={result.risk_level}
          score={result.risk_score}
          recommendation={result.recommendation}
          factors={result.factors}
          assessmentId={result.assessment_id}
          engine={result.engine}
          extra={<p className="mt-4 text-sm text-slate-400">Loan-to-income ratio: {Math.round(result.debt_ratio * 100)}%</p>}
        />
      )}
    </AppShell>
  );
}
