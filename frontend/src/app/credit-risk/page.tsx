"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";

export default function CreditRiskPage() {
  const API_URL =
    process.env.NEXT_PUBLIC_API_URL ||
    "https://finguard-ai-fullstack-production.up.railway.app";

  const [income, setIncome] = useState(50000);
  const [loanAmount, setLoanAmount] = useState(20000);
  const [creditScore, setCreditScore] = useState(720);

  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const predictRisk = async () => {
    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/predict-credit-risk`,
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

    setLoading(false);
  };

  return (
    <div className="flex min-h-screen bg-[#0B1120] text-white">
      <Sidebar />

      <main className="flex-1 p-8">
        <h1 className="text-5xl font-bold text-cyan-400">
          Credit Risk Intelligence
        </h1>

        <p className="mt-3 text-gray-400">
          AI-powered credit risk monitoring and loan default prediction.
        </p>

        <div className="mt-10 rounded-2xl bg-[#111827] p-8">
          <h2 className="text-3xl font-bold text-yellow-400">
            Credit Risk Prediction
          </h2>

          <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-3">
            <div>
              <label className="text-gray-300">Annual Income</label>

              <input
                type="number"
                value={income}
                onChange={(e) => setIncome(Number(e.target.value))}
                className="mt-2 w-full rounded-xl bg-[#1F2937] p-4 text-white outline-none"
              />
            </div>

            <div>
              <label className="text-gray-300">Loan Amount</label>

              <input
                type="number"
                value={loanAmount}
                onChange={(e) => setLoanAmount(Number(e.target.value))}
                className="mt-2 w-full rounded-xl bg-[#1F2937] p-4 text-white outline-none"
              />
            </div>

            <div>
              <label className="text-gray-300">Credit Score</label>

              <input
                type="number"
                value={creditScore}
                onChange={(e) => setCreditScore(Number(e.target.value))}
                className="mt-2 w-full rounded-xl bg-[#1F2937] p-4 text-white outline-none"
              />
            </div>
          </div>

          <button
            onClick={predictRisk}
            className="mt-8 rounded-xl bg-cyan-400 px-8 py-4 font-bold text-black transition hover:bg-cyan-300"
          >
            {loading ? "Analyzing..." : "Predict Credit Risk"}
          </button>

          {result && (
            <div className="mt-10 rounded-2xl bg-[#0F172A] p-8">
              <h3 className="text-3xl font-bold text-green-400">
                Prediction Result
              </h3>

              <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
                <div>
                  <p className="text-gray-400">Risk Level</p>

                  <h2 className="text-5xl font-bold text-red-400">
                    {result.risk_level}
                  </h2>
                </div>

                <div>
                  <p className="text-gray-400">Risk Score</p>

                  <h2 className="text-5xl font-bold text-yellow-400">
                    {result.risk_score}
                  </h2>
                </div>
              </div>

              <div className="mt-8">
                <p className="text-gray-400">AI Recommendation</p>

                <p className="mt-3 text-lg text-white">
                  {result.recommendation}
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}