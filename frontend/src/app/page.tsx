"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";

export default function DashboardPage() {

  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    fetch("http://localhost:8000/dashboard-metrics")
      .then((res) => res.json())
      .then((data) => setMetrics(data));
  }, []);

  if (!metrics) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0B1120] text-white">
        Loading FinGuard AI...
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#0B1120] text-white">

      <Sidebar />

      <main className="flex-1 p-8">

        <div className="flex items-center justify-between">

          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-cyan-400">
              Enterprise Banking Intelligence Platform
            </p>

            <h1 className="mt-3 text-5xl font-bold">
              Executive Dashboard
            </h1>

            <p className="mt-4 text-gray-400">
              Real-time banking intelligence and AI-powered risk monitoring.
            </p>
          </div>

          <button className="rounded-2xl bg-cyan-500 px-6 py-3 font-semibold text-black hover:bg-cyan-400">
            Generate AI Report
          </button>
        </div>

        {/* Metrics */}
        <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-4">

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">Risk Score</p>

            <h2 className="mt-3 text-5xl font-bold text-cyan-400">
              {metrics.risk_score}%
            </h2>

            <p className="mt-3 text-gray-500">
              Portfolio risk level
            </p>
          </div>

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">Fraud Alerts</p>

            <h2 className="mt-3 text-5xl font-bold text-red-400">
              {metrics.fraud_alerts}
            </h2>

            <p className="mt-3 text-gray-500">
              Active investigations
            </p>
          </div>

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">AML Cases</p>

            <h2 className="mt-3 text-5xl font-bold text-yellow-400">
              {metrics.aml_cases}
            </h2>

            <p className="mt-3 text-gray-500">
              Compliance watchlist
            </p>
          </div>

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">AI Predictions</p>

            <h2 className="mt-3 text-5xl font-bold text-green-400">
              {metrics.ai_predictions}
            </h2>

            <p className="mt-3 text-gray-500">
              Model decisions logged
            </p>
          </div>

        </div>

        {/* Risk Overview */}
        <div className="mt-10 grid grid-cols-1 gap-8 lg:grid-cols-2">

          <div className="rounded-2xl bg-[#111827] p-8">

            <h2 className="mb-6 text-2xl font-bold text-orange-300">
              Risk Intelligence Overview
            </h2>

            <div className="space-y-5">

              <div className="flex items-center justify-between rounded-xl bg-[#1F2937] p-5">
                <span>Credit Risk Exposure</span>

                <span className="font-bold text-cyan-400">
                  Medium
                </span>
              </div>

              <div className="flex items-center justify-between rounded-xl bg-[#1F2937] p-5">
                <span>Fraud Monitoring Status</span>

                <span className="font-bold text-red-400">
                  Elevated
                </span>
              </div>

              <div className="flex items-center justify-between rounded-xl bg-[#1F2937] p-5">
                <span>AML Compliance Watch</span>

                <span className="font-bold text-yellow-400">
                  Active
                </span>
              </div>

              <div className="flex items-center justify-between rounded-xl bg-[#1F2937] p-5">
                <span>Operational Health</span>

                <span className="font-bold text-green-400">
                  Stable
                </span>
              </div>

            </div>
          </div>

          {/* AI Copilot */}
          <div className="rounded-2xl bg-[#111827] p-8">

            <h2 className="mb-6 text-2xl font-bold text-orange-300">
              AI Executive Copilot
            </h2>

            <p className="leading-8 text-gray-300">
              FinGuard AI has detected elevated fraud activity and
              moderate credit risk exposure. Recommended action:
              prioritize fraud case review, monitor high-risk customer
              segments, and escalate AML watchlist cases for compliance review.
            </p>

            <div className="mt-8 rounded-2xl border border-cyan-500 bg-[#0F172A] p-6">

              <h3 className="text-lg font-bold text-cyan-400">
                Suggested Executive Action
              </h3>

              <p className="mt-3 leading-7 text-gray-300">
                Review fraud alerts within 24 hours and generate
                a detailed portfolio risk report for senior management.
              </p>
            </div>

            <button className="mt-8 rounded-2xl bg-cyan-500 px-6 py-3 font-semibold text-black hover:bg-cyan-400">
              Ask Copilot
            </button>
          </div>

        </div>

        {/* Workflow */}
        <section className="mt-10 rounded-2xl bg-[#111827] p-8">

          <h2 className="mb-8 text-2xl font-bold text-orange-300">
            AI Platform Workflow
          </h2>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-4">

            <div className="rounded-2xl bg-[#1F2937] p-6">
              <h3 className="text-xl font-bold text-cyan-400">
                1. Data Input
              </h3>

              <p className="mt-3 text-gray-400">
                Banking, customer, transaction, and compliance data.
              </p>
            </div>

            <div className="rounded-2xl bg-[#1F2937] p-6">
              <h3 className="text-xl font-bold text-cyan-400">
                2. ML Scoring
              </h3>

              <p className="mt-3 text-gray-400">
                Credit risk, fraud anomaly, and AML risk models.
              </p>
            </div>

            <div className="rounded-2xl bg-[#1F2937] p-6">
              <h3 className="text-xl font-bold text-cyan-400">
                3. AI Reasoning
              </h3>

              <p className="mt-3 text-gray-400">
                Explainable AI, copilot insights, and executive summaries.
              </p>
            </div>

            <div className="rounded-2xl bg-[#1F2937] p-6">
              <h3 className="text-xl font-bold text-cyan-400">
                4. Action Logs
              </h3>

              <p className="mt-3 text-gray-400">
                Audit monitoring, operational alerts, and executive actions.
              </p>
            </div>

          </div>

        </section>

      </main>
    </div>
  );
}