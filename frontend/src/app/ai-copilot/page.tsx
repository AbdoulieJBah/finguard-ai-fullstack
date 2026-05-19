"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";

export default function AICopilotPage() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const askCopilot = async () => {
    if (!question.trim()) return;

    setLoading(true);

    try {
      const response = await fetch(
        "http://localhost:8000/copilot",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question,
          }),
        }
      );

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        `You: ${question}`,
        `FinGuard AI: ${data.response}`,
      ]);

      setQuestion("");

    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        "FinGuard AI: Unable to connect to backend service.",
      ]);
    }

    setLoading(false);
  };

  return (
    <div className="flex min-h-screen bg-[#0B1120] text-white">
      <Sidebar />

      <main className="flex-1 p-8">
        <h1 className="text-4xl font-bold text-cyan-400">
          AI Banking Copilot
        </h1>

        <p className="mt-3 text-gray-400">
          Conversational AI for fraud detection, AML monitoring, audit analysis, and executive banking intelligence.
        </p>

        <div className="mt-10 rounded-2xl bg-[#111827] p-8">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask FinGuard AI about fraud, AML, risk exposure, compliance, or banking intelligence..."
            className="h-36 w-full rounded-2xl border border-cyan-500 bg-[#1F2937] p-5 text-white outline-none"
          />

          <button
            onClick={askCopilot}
            disabled={loading}
            className="mt-5 rounded-2xl bg-cyan-500 px-6 py-3 font-semibold text-black hover:bg-cyan-400 disabled:opacity-50"
          >
            {loading ? "Analyzing..." : "Ask Copilot"}
          </button>
        </div>

        <div className="mt-10 space-y-5">
          {messages.map((message, index) => (
            <div
              key={index}
              className="rounded-2xl bg-[#111827] p-5 text-gray-300"
            >
              {message}
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}