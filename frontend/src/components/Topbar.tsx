"use client";

import { useEffect, useState } from "react";

export default function Topbar() {
  const [time, setTime] = useState("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();

      setTime(
        now.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })
      );
    };

    updateTime();

    const interval = setInterval(updateTime, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="mb-8 flex flex-col gap-6 rounded-2xl bg-[#111827] p-6 md:flex-row md:items-center md:justify-between">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-cyan-400">
          FinGuard AI Enterprise Platform
        </p>

        <h2 className="mt-2 text-3xl font-bold">
          Executive Banking Intelligence
        </h2>
      </div>

      <div className="flex items-center gap-6">
        <div className="rounded-xl bg-[#1F2937] px-4 py-3">
          <p className="text-sm text-gray-400">AI Status</p>

          <p className="font-bold text-green-400">
            Operational
          </p>
        </div>

        <div className="rounded-xl bg-[#1F2937] px-4 py-3">
          <p className="text-sm text-gray-400">Local Time</p>

          <p className="font-bold text-cyan-400">
            {time}
          </p>
        </div>

        <div className="relative rounded-full bg-cyan-500 px-5 py-3 font-bold text-black">
          4

          <span className="absolute -right-1 -top-1 h-4 w-4 rounded-full bg-red-500"></span>
        </div>

        <div className="rounded-xl bg-[#1F2937] px-5 py-3">
          <p className="text-sm text-gray-400">
            Executive User
          </p>

          <p className="font-bold text-white">
            Abdoulie Bah
          </p>
        </div>
      </div>
    </div>
  );
}
