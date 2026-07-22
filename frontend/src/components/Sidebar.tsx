"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Bot, Building2, CreditCard, FileClock, HeartPulse, Landmark, LogOut, Send, ShieldAlert, UserRound } from "lucide-react";
import { useAuth } from "./AuthProvider";

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const links = [
    ["/", "Overview", BarChart3], ["/accounts", "Accounts", Landmark], ["/transfers", "Payments", Send],
    ["/credit-risk", "Credit Risk", CreditCard], ["/fraud-detection", "Fraud Detection", ShieldAlert],
    ["/aml-monitoring", "AML Monitoring", Building2], ["/ai-copilot", "AI Copilot", Bot],
    ["/audit-logs", "Audit Logs", FileClock], ["/system-health", "System Health", HeartPulse],
  ] as const;
  return (
    <aside className="hidden min-h-screen w-64 shrink-0 border-r border-white/5 bg-[#0d1424] p-5 md:flex md:flex-col">
      <Link href="/" className="mb-8 flex items-center gap-3 text-xl font-bold"><span className="grid h-10 w-10 place-items-center rounded-xl bg-cyan-400 text-slate-950"><Landmark size={21}/></span>FinGuard</Link>
      <nav className="space-y-1 text-sm font-medium">
        {links.map(([href, label, Icon]) => <Link key={href} href={href} className={`flex items-center gap-3 rounded-xl px-3 py-2.5 transition ${pathname === href ? "bg-cyan-400/10 text-cyan-300" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}><Icon size={18}/>{label}</Link>)}
      </nav>
      <div className="mt-auto border-t border-white/5 pt-5">
        {user ? <><div className="mb-3 flex items-center gap-3"><UserRound className="text-cyan-300"/><div className="min-w-0"><p className="truncate text-sm font-semibold">{user.name}</p><p className="truncate text-xs text-slate-500">{user.role}</p></div></div><button onClick={logout} className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm text-slate-400 hover:text-white"><LogOut size={16}/>Sign out</button></> : <Link href="/login" className="block rounded-xl bg-cyan-400 px-4 py-2 text-center font-semibold text-slate-950">Secure sign in</Link>}
      </div>
    </aside>
  );
}
