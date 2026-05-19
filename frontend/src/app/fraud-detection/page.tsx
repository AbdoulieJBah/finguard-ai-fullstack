"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";

export default function FraudDetectionPage() {
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/fraud-alerts")
      .then((res) => res.json())
      .then((data) => setAlerts(data));
  }, []);

  return (
    <div className="flex min-h-screen bg-[#0B1120] text-white">
      <Sidebar />

      <main className="flex-1 p-8">
        <h1 className="text-4xl font-bold text-cyan-400">
          Fraud Detection Intelligence
        </h1>

        <p className="mt-3 text-gray-400">
          Real-time fraud monitoring and anomaly intelligence system.
        </p>

        <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">Fraud Alerts</p>

            <h2 className="mt-3 text-4xl font-bold text-red-400">
              {alerts.length}
            </h2>
          </div>

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">Monitoring Status</p>

            <h2 className="mt-3 text-4xl font-bold text-yellow-400">
              Active
            </h2>
          </div>

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">Risk Engine</p>

            <h2 className="mt-3 text-4xl font-bold text-cyan-400">
              Online
            </h2>
          </div>
        </div>

        <div className="mt-10 rounded-2xl bg-[#111827] p-8">
          <h2 className="mb-6 text-2xl font-bold text-orange-300">
            Fraud Alert Queue
          </h2>

          <div className="space-y-5">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="rounded-2xl bg-[#1F2937] p-6"
              >
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">

                  <div>
                    <h3 className="text-xl font-bold">
                      {alert.customer}
                    </h3>

                    <p className="mt-2 text-gray-400">
                      {alert.reason}
                    </p>
                  </div>

                  <div className="text-right">
                    <p className="text-lg font-bold text-cyan-400">
                      €{alert.amount}
                    </p>

                    <span className="mt-2 inline-block rounded-full bg-red-500 px-4 py-1 text-sm font-semibold">
                      {alert.risk}
                    </span>
                  </div>

                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}