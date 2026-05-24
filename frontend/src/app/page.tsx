"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";

interface DashboardMetrics {
  risk_score: number;
  fraud_alerts: number;
  aml_cases: number;
  ai_predictions: number;
}

export default function HomePage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);

  const API_URL =
    process.env.NEXT_PUBLIC_API_URL ||
    "https://finguard-ai-fullstack-production.up.railway.app";

  useEffect(() => {
    const fallbackData = {
      risk_score: 82,
      fraud_alerts: 24,
      aml_cases: 13,
      ai_predictions: 1284,
    };

    const controller = new AbortController();

    const timer = setTimeout(() => {
      controller.abort();
      setMetrics(fallbackData);
    }, 5000);

    fetch(`${API_URL}/dashboard-metrics`, {
      signal: controller.signal,
    })
      .then((res) => {
        if (!res.ok) throw new Error("Backend response failed");
        return res.json();
      })
      .then((data) => {
        clearTimeout(timer);
        setMetrics(data);
      })
      .catch(() => {
        clearTimeout(timer);
        setMetrics(fallbackData);
      });

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [API_URL]);

  if (!metrics) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0B1120] text-2xl text-white">
        Loading FinGuard AI...
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#0B1120] text-white">
      <Sidebar />

      <main className="flex-1 p-8">
        <p className="text-sm uppercase tracking-[0.3em] text-cyan-400">
          Enterprise Banking Intelligence Platform
        </p>

        <h1 className="mt-3 text-5xl font-bold">Executive Dashboard</h1>

        <p className="mt-4 text-gray-400">
          Real-time banking intelligence and AI-powered risk monitoring.
        </p>

        <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-4">
          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">Risk Score</p>
            <h2 className="mt-3 text-5xl font-bold text-cyan-400">
              {metrics.risk_score}%
            </h2>
          </div>

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">Fraud Alerts</p>
            <h2 className="mt-3 text-5xl font-bold text-red-400">
              {metrics.fraud_alerts}
            </h2>
          </div>

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">AML Cases</p>
            <h2 className="mt-3 text-5xl font-bold text-yellow-400">
              {metrics.aml_cases}
            </h2>
          </div>

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">AI Predictions</p>
            <h2 className="mt-3 text-5xl font-bold text-green-400">
              {metrics.ai_predictions}
            </h2>
          </div>
        </div>
      </main>
    </div>
  );
}