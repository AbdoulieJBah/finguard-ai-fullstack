"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<any[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/audit-logs")
      .then((res) => res.json())
      .then((data) => setLogs(data));
  }, []);

  return (
    <div className="flex min-h-screen bg-[#0B1120] text-white">
      <Sidebar />

      <main className="flex-1 p-8">
        <h1 className="text-4xl font-bold text-cyan-400">
          Audit Logs & Monitoring
        </h1>

        <p className="mt-3 text-gray-400">
          Operational audit trails, AI decisions, fraud investigations, and compliance monitoring history.
        </p>

        <div className="mt-10 rounded-2xl bg-[#111827] p-8">
          <h2 className="mb-6 text-2xl font-bold text-orange-300">
            System Activity Logs
          </h2>

          <div className="space-y-4">
            {logs.map((log, index) => (
              <div
                key={index}
                className="flex flex-col justify-between rounded-xl bg-[#1F2937] p-5 md:flex-row md:items-center"
              >
                <div>
                  <h3 className="font-semibold">{log.action}</h3>

                  <p className="mt-1 text-sm text-gray-400">
                    Performed by: {log.user}
                  </p>
                </div>

                <div className="mt-4 flex items-center gap-4 md:mt-0">
                  <span className="text-sm text-gray-400">
                    {log.time}
                  </span>

                  <span className="rounded-full bg-cyan-500 px-4 py-1 text-sm font-semibold text-black">
                    {log.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">Audit Events</p>
            <h2 className="mt-3 text-4xl font-bold text-cyan-400">
              {logs.length}
            </h2>
          </div>

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">AI Decisions Logged</p>
            <h2 className="mt-3 text-4xl font-bold text-green-400">
              842
            </h2>
          </div>

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">Security Incidents</p>
            <h2 className="mt-3 text-4xl font-bold text-red-400">
              7
            </h2>
          </div>
        </div>
      </main>
    </div>
  );
}