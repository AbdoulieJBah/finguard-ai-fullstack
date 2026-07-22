"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";

export default function AMLMonitoringPage() {
  const API_URL =
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000";

  const [transactionAmount, setTransactionAmount] = useState(25000);
  const [countryRisk, setCountryRisk] = useState("High");
  const [suspiciousTransfers, setSuspiciousTransfers] = useState(5);

  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const predictAMLRisk = async () => {
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/predict-aml-risk`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          transaction_amount: transactionAmount,
          country_risk: countryRisk,
          suspicious_transfers: suspiciousTransfers,
        }),
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("AML prediction failed:", error);
    }

    setLoading(false);
  };

  return (
    <div className="flex min-h-screen bg-[#0B1120] text-white">
      <Sidebar />

      <main className="flex-1 p-8">
        <h1 className="text-5xl font-bold text-cyan-400">
          AML Monitoring Center
        </h1>

        <p className="mt-3 text-gray-400">
          Anti-money laundering intelligence and compliance monitoring.
        </p>

        <div className="mt-10 rounded-2xl bg-[#111827] p-8">
          <h2 className="text-3xl font-bold text-yellow-400">
            AML Risk Prediction
          </h2>

          <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-3">
            <div>
              <label className="text-gray-300">
                Transaction Amount
              </label>

              <input
                type="number"
                value={transactionAmount}
                onChange={(e) =>
                  setTransactionAmount(Number(e.target.value))
                }
                className="mt-2 w-full rounded-xl bg-[#1F2937] p-4 text-white outline-none"
              />
            </div>

            <div>
              <label className="text-gray-300">Country Risk</label>

              <select
                value={countryRisk}
                onChange={(e) => setCountryRisk(e.target.value)}
                className="mt-2 w-full rounded-xl bg-[#1F2937] p-4 text-white outline-none"
              >
                <option>Low</option>
                <option>Medium</option>
                <option>High</option>
              </select>
            </div>

            <div>
              <label className="text-gray-300">
                Suspicious Transfers
              </label>

              <input
                type="number"
                value={suspiciousTransfers}
                onChange={(e) =>
                  setSuspiciousTransfers(Number(e.target.value))
                }
                className="mt-2 w-full rounded-xl bg-[#1F2937] p-4 text-white outline-none"
              />
            </div>
          </div>

          <button
            onClick={predictAMLRisk}
            className="mt-8 rounded-xl bg-cyan-400 px-8 py-4 font-bold text-black transition hover:bg-cyan-300"
          >
            {loading ? "Analyzing..." : "Predict AML Risk"}
          </button>

          {result && (
            <div className="mt-10 rounded-2xl bg-[#0F172A] p-8">
              <h3 className="text-3xl font-bold text-green-400">
                Prediction Result
              </h3>

              <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
                <div>
                  <p className="text-gray-400">AML Risk Level</p>

                  <h2 className="text-5xl font-bold text-red-400">
                    {result.aml_level}
                  </h2>
                </div>

                <div>
                  <p className="text-gray-400">AML Score</p>

                  <h2 className="text-5xl font-bold text-yellow-400">
                    {result.aml_score}
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
