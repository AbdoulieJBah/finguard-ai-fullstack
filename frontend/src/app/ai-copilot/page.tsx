"use client";

import { useEffect, useState } from "react";

interface DashboardMetrics {
  risk_score: number;
  fraud_alerts: number;
  aml_cases: number;
  ai_predictions: number;
}

export default function HomePage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);

  const API_URL =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetch(`${API_URL}/dashboard-metrics`)
      .then((res) => res.json())
      .then((data) => setMetrics(data))
      .catch((error) => {
        console.error("Backend connection failed:", error);

        // fallback demo data
        setMetrics({
          risk_score: 82,
          fraud_alerts: 24,
          aml_cases: 13,
          ai_predictions: 1284,
        });
      });
  }, [API_URL]);

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-screen bg-black text-white text-2xl">
        Loading FinGuard AI...
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white p-10">
      <h1 className="text-4xl font-bold mb-8 text-center">
        FinGuard AI Dashboard
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-900 rounded-2xl p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-2">Risk Score</h2>
          <p className="text-5xl font-bold text-green-400">
            {metrics.risk_score}
          </p>
        </div>

        <div className="bg-gray-900 rounded-2xl p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-2">Fraud Alerts</h2>
          <p className="text-5xl font-bold text-red-400">
            {metrics.fraud_alerts}
          </p>
        </div>

        <div className="bg-gray-900 rounded-2xl p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-2">AML Cases</h2>
          <p className="text-5xl font-bold text-yellow-400">
            {metrics.aml_cases}
          </p>
        </div>

        <div className="bg-gray-900 rounded-2xl p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-2">AI Predictions</h2>
          <p className="text-5xl font-bold text-blue-400">
            {metrics.ai_predictions}
          </p>
        </div>
      </div>
    </main>
  );
}