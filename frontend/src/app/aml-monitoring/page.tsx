"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";

export default function AMLMonitoringPage() {
  const [cases, setCases] = useState<any[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/aml-cases")
      .then((res) => res.json())
      .then((data) => setCases(data));
  }, []);

  return (
    <div className="flex min-h-screen bg-[#0B1120] text-white">
      <Sidebar />

      <main className="flex-1 p-8">
        <h1 className="text-4xl font-bold text-cyan-400">
          AML Monitoring Center
        </h1>

        <p className="mt-3 text-gray-400">
          Anti-money laundering intelligence, compliance tracking, and case monitoring.
        </p>

        <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">AML Cases</p>
            <h2 className="mt-3 text-4xl font-bold text-yellow-400">
              {cases.length}
            </h2>
          </div>

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">Compliance Status</p>
            <h2 className="mt-3 text-4xl font-bold text-green-400">
              Active
            </h2>
          </div>

          <div className="rounded-2xl bg-[#111827] p-6">
            <p className="text-gray-400">AML Engine</p>
            <h2 className="mt-3 text-4xl font-bold text-cyan-400">
              Online
            </h2>
          </div>
        </div>

        <div className="mt-10 rounded-2xl bg-[#111827] p-8">
          <h2 className="mb-6 text-2xl font-bold text-orange-300">
            AML Investigation Queue
          </h2>

          <div className="space-y-5">
            {cases.map((item) => (
              <div key={item.id} className="rounded-2xl bg-[#1F2937] p-6">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <h3 className="text-xl font-bold">{item.case}</h3>
                    <p className="mt-2 text-gray-400">
                      Status: {item.status}
                    </p>
                  </div>

                  <span className="rounded-full bg-yellow-500 px-4 py-1 text-sm font-semibold text-black">
                    {item.level}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}