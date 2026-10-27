"use client";

import { FormEvent, useState } from "react";
import AppShell, { ErrorNotice, PageHeader } from "@/components/AppShell";
import { inputClass, primaryButtonClass } from "@/components/RiskWidgets";
import { api } from "@/lib/api";

const SUGGESTIONS = ["What is the fraud situation?", "How many AML cases are open?", "What is the average risk score?", "What is my balance?"];

export default function CopilotPage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function ask(text: string) {
    if (text.trim().length < 2) return;
    setLoading(true);
    setError("");
    setAnswer("");
    try {
      const data = await api<{ response: string }>("/copilot", { method: "POST", body: JSON.stringify({ question: text }) });
      setAnswer(data.response);
    } catch (e) {
      setError(e instanceof Error ? e.message : "The copilot could not answer");
    } finally {
      setLoading(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void ask(question);
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Assistant"
        title="FinGuard Copilot"
        description="Ask about fraud alerts, AML cases, risk scores or your balances. Answers use live figures from the database; the current version routes questions by keyword."
      />
      <form onSubmit={submit} className="mt-8 rounded-2xl bg-[#111827] p-5 sm:p-8">
        <label className="block text-sm text-slate-300">
          Your question
          <textarea value={question} onChange={(e) => setQuestion(e.target.value)} maxLength={500} placeholder="Example: What is the fraud situation?" className={`${inputClass} h-32`} />
        </label>
        <div className="mt-4 flex flex-wrap gap-2">
          {SUGGESTIONS.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => {
                setQuestion(suggestion);
                void ask(suggestion);
              }}
              className="rounded-full border border-white/10 px-3 py-1.5 text-sm text-slate-300 hover:border-cyan-400 hover:text-white"
            >
              {suggestion}
            </button>
          ))}
        </div>
        <button type="submit" disabled={loading || question.trim().length < 2} className={primaryButtonClass}>
          {loading ? "Thinking…" : "Ask"}
        </button>
        {error && <ErrorNotice message={error} />}
      </form>
      {answer && (
        <section className="mt-8 rounded-2xl border border-white/10 bg-[#0F172A] p-5 sm:p-8" aria-live="polite">
          <h2 className="text-xl font-bold text-green-400">Answer</h2>
          <p className="mt-4 text-lg leading-8">{answer}</p>
        </section>
      )}
    </AppShell>
  );
}
