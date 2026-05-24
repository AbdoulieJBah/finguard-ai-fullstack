import Link from "next/link";

export default function Sidebar() {
  return (
    <aside className="hidden min-h-screen w-64 bg-[#111827] p-6 md:block">
      <h1 className="mb-10 text-3xl font-bold text-cyan-400">
        FinGuard AI
      </h1>

      <nav className="space-y-6 text-white font-medium">
        <Link href="/" className="block rounded-lg p-3 hover:bg-[#1F2937] hover:text-cyan-400">
          Dashboard
        </Link>

        <Link href="/credit-risk" className="block rounded-lg p-3 hover:bg-[#1F2937] hover:text-cyan-400">
          Credit Risk
        </Link>

        <Link href="/fraud-detection" className="block rounded-lg p-3 hover:bg-[#1F2937] hover:text-cyan-400">
          Fraud Detection
        </Link>

        <Link href="/aml-monitoring" className="block rounded-lg p-3 hover:bg-[#1F2937] hover:text-cyan-400">
          AML Monitoring
        </Link>

        <Link href="/ai-copilot" className="block rounded-lg p-3 hover:bg-[#1F2937] hover:text-cyan-400">
          AI Copilot
        </Link>

        <Link href="/audit-logs" className="block rounded-lg p-3 hover:bg-[#1F2937] hover:text-cyan-400">
          Audit Logs
        </Link>

        <Link href="/system-health" className="block rounded-lg p-3 hover:bg-[#1F2937] hover:text-cyan-400">
          System Health
        </Link>
      </nav>
    </aside>
  );
}