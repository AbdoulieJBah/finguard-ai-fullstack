"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";

export default function CreditRiskPage() {
  const [income, setIncome] = useState("");
  const [loanAmount, setLoanAmount] = useState("");
  const [creditScore, setCreditScore] = useState("");

  const [result, setResult] = useState<any>(null);

  const predictRisk = async () => {
    try {
      const response = await fetch(
        "http://localhost:8000/predict-credit-risk",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            income,
            loan_amount: loanAmount,
            credit_score: creditScore,
          }),
        }
      );

      const data = await response.json();
      setResult(data);

    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div className="flex min-h-screen bg-[#0B1120] text-white">
      <Sidebar />

      <main className="flex-1 p-8">
        <h1 className="text-4xl font-bold text-cyan-400">
          Credit Risk Intelligence
        </h1>

        <p className="mt-3 text-gray-400">
          AI-powered credit risk monitoring and loan default prediction.
        </p>

        {/* Input Form */}
        <div className="mt-10 rounded-2xl bg-[#111827] p-8">
          <h2 className="mb-6 text-2xl font-bold text-orange-300">
            Credit Risk Prediction
          </h2>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">

            <div>
              <label className="mb-2 block text-sm text-gray-400">
                Annual Income
              </label>

              <input
                type="number"
                value={income}
                onChange={(e) => setIncome(e.target.value)}
                placeholder="50000"
                className="w-full rounded-xl bg-[#1F2937] p-4 outline-none"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm text-gray-400">
                Loan Amount
              </label>

              <input
                type="number"
                value={loanAmount}
                onChange={(e) => setLoanAmount(e.target.value)}
                placeholder="20000"
                className="w-full rounded-xl bg-[#1F2937] p-4 outline-none"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm text-gray-400">
                Credit Score
              </label>

              <input
                type="number"
                value={creditScore}
                onChange={(e) => setCreditScore(e.target.value)}
                placeholder="720"
                className="w-full rounded-xl bg-[#1F2937] p-4 outline-none"
              />
            </div>

          </div>

          <button
            onClick={predictRisk}
            className="mt-8 rounded-2xl bg-cyan-500 px-6 py-3 font-semibold text-black hover:bg-cyan-400"
          >
            Predict Credit Risk
          </button>
        </div>

        {/* Prediction Result */}
        {result && (
          <div className="mt-10 rounded-2xl bg-[#111827] p-8">
            <h2 className="mb-6 text-2xl font-bold text-cyan-400">
              AI Risk Prediction Result
            </h2>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-4">

              <div className="rounded-2xl bg-[#1F2937] p-6">
                <p className="text-gray-400">Risk Level</p>

                <h3 className="mt-3 text-3xl font-bold text-red-400">
                  {result.risk_level}
                </h3>
              </div>

              <div className="rounded-2xl bg-[#1F2937] p-6">
                <p className="text-gray-400">Risk Score</p>

                <h3 className="mt-3 text-3xl font-bold text-yellow-400">
                  {result.risk_score}
                </h3>
              </div>

              <div className="rounded-2xl bg-[#1F2937] p-6">
                <p className="text-gray-400">Debt Ratio</p>

                <h3 className="mt-3 text-3xl font-bold text-cyan-400">
                  {result.debt_ratio}
                </h3>
              </div>

              <div className="rounded-2xl bg-[#1F2937] p-6">
                <p className="text-gray-400">Credit Score</p>

                <h3 className="mt-3 text-3xl font-bold text-green-400">
                  {result.credit_score}
                </h3>
              </div>

            </div>

            <div className="mt-8 rounded-2xl border border-cyan-500 bg-[#0F172A] p-6">
              <h3 className="mb-3 text-xl font-bold text-cyan-400">
                AI Recommendation
              </h3>

              <p className="text-gray-300 leading-8">
                {result.recommendation}
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}