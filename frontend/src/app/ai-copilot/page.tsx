"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";

export default function AICopilotPage() {
  const API_URL =
    process.env.NEXT_PUBLIC_API_URL ||
    "https://finguard-ai-fullstack-production.up.railway.app";

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const askCopilot = async () => {
    if (!question.trim()) return;

    setLoading(true);
    setAnswer("");

    try {
      const response = await fetch(`${API_URL}/copilot`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
        }),
      });

      const data = await response.json();
      setAnswer(data.response);
    } catch (error) {
      console.error("Copilot request failed:", error);
      setAnswer("Unable to connect to FinGuard AI backend.");
    }

    setLoading(false);
  };

  return (
    <div className="flex min-h-screen bg-[#0B1120] text-white">
      <Sidebar />

      <main className="flex-1 p-8">
        <h1 className="text-5xl font-bold text-cyan-400">
          AI Banking Copilot
        </h1>

        <p className="mt-3 text-gray-400">
          Ask questions about credit risk, fraud detection, AML monitoring, and audit intelligence.
        </p>

        <div className="mt-10 rounded-2xl bg-[#111827] p-8">
          <h2 className="text-3xl font-bold text-yellow-400">
            Ask FinGuard AI
          </h2>

          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Example: What is the current fraud risk?"
            className="mt-6 h-40 w-full rounded-xl bg-[#1F2937] p-4 text-white outline-none"
          />

          <button
            onClick={askCopilot}
            className="mt-6 rounded-xl bg-cyan-400 px-8 py-4 font-bold text-black transition hover:bg-cyan-300"
          >
            {loading ? "Thinking..." : "Ask Copilot"}
          </button>

          {answer && (
            <div className="mt-10 rounded-2xl bg-[#0F172A] p-8">
              <h3 className="text-3xl font-bold text-green-400">
                FinGuard AI Response
              </h3>

              <p className="mt-6 text-lg leading-8 text-white">
                {answer}
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}