"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface DashboardMetrics {
  risk_score: number;
  fraud_alerts: number;
  aml_cases: number;
  ai_predictions: number;
}

interface RiskTrend {
  month: string;
  risk: number;
  fraud: number;
  aml: number;
}

export default function DashboardPage() {
  const API_URL =
    process.env.NEXT_PUBLIC_API_URL ||
    "https://finguard-ai-fullstack-production.up.railway.app";

  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [trends, setTrends] = useState<RiskTrend[]>([]);

  useEffect(() => {
    fetch(`${API_URL}/dashboard-metrics`)
      .then((res) => res.json())
      .then((data) => setMetrics(data))
      .catch(() =>
        setMetrics({
          risk_score: 82,
          fraud_alerts: 24,
          aml_cases: 13,
          ai_predictions: 1284,
        })
      );

    fetch(`${API_URL}/risk-trends`)
      .then((res) => res.json())
      .then((data) => setTrends(data))
      .catch(() =>
        setTrends([
          { month: "Jan", risk: 45, fraud: 20, aml: 15 },
          { month: "Feb", risk: 52, fraud: 25, aml: 18 },
          { month: "Mar", risk: 48, fraud: 22, aml: 17 },
          { month: "Apr", risk: 70, fraud: 40, aml: 29 },
          { month: "May", risk: 66, fraud: 38, aml: 31 },
          { month: "Jun", risk: 82, fraud: 50, aml: 36 },
        ])
      );
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
          Real-time banking intelligence, fraud analytics, AML monitoring, and AI-powered risk insights.
        </p>

        <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-4">
          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">Risk Score</p>
            <h2 className="mt-3 text-5xl font-bold text-cyan-400">
              {metrics.risk_score}%
            </h2>
            <p className="mt-2 text-sm text-gray-500">Portfolio risk level</p>
          </div>

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">Fraud Alerts</p>
            <h2 className="mt-3 text-5xl font-bold text-red-400">
              {metrics.fraud_alerts}
            </h2>
            <p className="mt-2 text-sm text-gray-500">Active investigations</p>
          </div>

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">AML Cases</p>
            <h2 className="mt-3 text-5xl font-bold text-yellow-400">
              {metrics.aml_cases}
            </h2>
            <p className="mt-2 text-sm text-gray-500">Compliance watchlist</p>
          </div>

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">AI Predictions</p>
            <h2 className="mt-3 text-5xl font-bold text-green-400">
              {metrics.ai_predictions}
            </h2>
            <p className="mt-2 text-sm text-gray-500">Model decisions logged</p>
          </div>
        </div>

        <div className="mt-10 grid grid-cols-1 gap-8 xl:grid-cols-2">
          <div className="rounded-2xl bg-[#111827] p-8">
            <h2 className="text-2xl font-bold text-cyan-400">
              Risk Analytics Trend
            </h2>

            <p className="mt-2 text-gray-400">
              Monthly AI-generated portfolio risk movement.
            </p>

            <div className="mt-8 h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="month" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="risk"
                    stroke="#22D3EE"
                    strokeWidth={4}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl bg-[#111827] p-8">
            <h2 className="text-2xl font-bold text-red-400">
              Fraud Detection Trend
            </h2>

            <p className="mt-2 text-gray-400">
              Suspicious activity trend from AI fraud monitoring.
            </p>

            <div className="mt-8 h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="month" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="fraud"
                    stroke="#F87171"
                    fill="#F87171"
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="mt-10 rounded-2xl bg-[#111827] p-8">
          <h2 className="text-2xl font-bold text-yellow-400">
            AML Compliance Trend
          </h2>

          <p className="mt-2 text-gray-400">
            AML case monitoring and compliance risk trend.
          </p>

          <div className="mt-8 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="month" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="aml"
                  stroke="#FACC15"
                  strokeWidth={4}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="mt-10 rounded-2xl bg-[#111827] p-8">
          <h2 className="text-2xl font-bold text-orange-300">
            Executive AI Summary
          </h2>

          <p className="mt-4 leading-8 text-gray-300">
            FinGuard AI detected increased portfolio risk, elevated fraud activity, and active AML monitoring cases.
            Recommended action: prioritize fraud investigations, review high-risk credit profiles, and escalate AML cases for compliance review.
          </p>
        </div>
      </main>
    </div>
  );
}