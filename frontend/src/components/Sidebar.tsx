"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { BarChart3, Bot, Building2, CreditCard, FileClock, HeartPulse, Landmark, LogOut, Menu, Send, ShieldAlert, UserRound, X } from "lucide-react";
import { useAuth } from "./AuthProvider";

const links = [
  ["/", "Overview", BarChart3], ["/accounts", "Accounts", Landmark], ["/transfers", "Payments", Send],
  ["/credit-risk", "Credit Risk", CreditCard], ["/fraud-detection", "Fraud Detection", ShieldAlert],
  ["/aml-monitoring", "AML Monitoring", Building2], ["/ai-copilot", "AI Copilot", Bot],
  ["/audit-logs", "Audit Logs", FileClock], ["/system-health", "System Health", HeartPulse],
] as const;

function Logo() {
  return <><span className="grid h-10 w-10 place-items-center rounded-xl bg-cyan-400 text-slate-950"><Landmark size={21}/></span>FinGuard</>;
}

function NavContent({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  const { user, logout } = useAuth();
  return (
    <>
      <nav className="space-y-1 text-sm font-medium">
        {links.map(([href, label, Icon]) => <Link key={href} href={href} onClick={onNavigate} aria-current={pathname === href ? "page" : undefined} className={`flex items-center gap-3 rounded-xl px-3 py-2.5 transition ${pathname === href ? "bg-cyan-400/10 text-cyan-300" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}><Icon size={18}/>{label}</Link>)}
      </nav>
      <div className="mt-auto border-t border-white/5 pt-5">
        {user ? <><div className="mb-3 flex items-center gap-3"><UserRound className="text-cyan-300"/><div className="min-w-0"><p className="truncate text-sm font-semibold">{user.name}</p><p className="truncate text-xs text-slate-500">{user.role}</p></div></div><button onClick={logout} className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm text-slate-400 hover:text-white"><LogOut size={16}/>Sign out</button></> : <Link href="/login" className="block rounded-xl bg-cyan-400 px-4 py-2 text-center font-semibold text-slate-950">Secure sign in</Link>}
      </div>
    </>
  );
}

export default function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const openButton = useRef<HTMLButtonElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const wasOpen = useRef(false);
  const current = links.find(([href]) => href === pathname)?.[1] ?? "FinGuard";

  // Close the mobile menu after navigating to another section.
  useEffect(() => { setOpen(false); }, [pathname]);

  // While the menu is open: lock page scroll, close on Escape, and move focus into the menu.
  useEffect(() => {
    if (!open) {
      if (wasOpen.current) openButton.current?.focus();
      wasOpen.current = false;
      return;
    }
    wasOpen.current = true;
    closeButton.current?.focus();
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", onKey);
    return () => { document.body.style.overflow = previousOverflow; window.removeEventListener("keydown", onKey); };
  }, [open]);

  // Return to the desktop layout cleanly if the window is widened while the menu is open.
  useEffect(() => {
    const desktop = window.matchMedia("(min-width: 768px)");
    const onChange = () => { if (desktop.matches) setOpen(false); };
    desktop.addEventListener("change", onChange);
    return () => desktop.removeEventListener("change", onChange);
  }, []);

  return (
    <>
      {/* Mobile top bar */}
      <header className="sticky top-0 z-40 flex h-16 shrink-0 items-center justify-between gap-3 border-b border-white/5 bg-[#0d1424]/95 px-4 backdrop-blur md:hidden">
        <Link href="/" className="flex min-w-0 items-center gap-3 text-lg font-bold"><Logo/></Link>
        <div className="flex min-w-0 items-center gap-2">
          <span className="truncate text-sm text-slate-400">{current}</span>
          <button ref={openButton} type="button" onClick={() => setOpen(true)} aria-label="Open navigation menu" aria-expanded={open} aria-controls="mobile-nav" className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-white/10 text-slate-200 hover:bg-white/5">
            <Menu size={22}/>
          </button>
        </div>
      </header>

      {/* Mobile slide-in menu */}
      <div className={`fixed inset-0 z-50 md:hidden ${open ? "visible" : "invisible transition-[visibility] duration-300"}`} aria-hidden={!open}>
        <button type="button" tabIndex={-1} aria-label="Close navigation menu" onClick={() => setOpen(false)} className={`absolute inset-0 bg-black/60 transition-opacity duration-300 ${open ? "opacity-100" : "opacity-0"}`}/>
        <aside id="mobile-nav" role="dialog" aria-modal="true" aria-label="Navigation" className={`absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col overflow-y-auto border-r border-white/5 bg-[#0d1424] p-5 shadow-2xl transition-transform duration-300 ${open ? "translate-x-0" : "-translate-x-full"}`}>
          <div className="mb-8 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3 text-xl font-bold"><Logo/></Link>
            <button ref={closeButton} type="button" onClick={() => setOpen(false)} aria-label="Close navigation menu" className="grid h-10 w-10 place-items-center rounded-xl text-slate-400 hover:bg-white/5 hover:text-white"><X size={22}/></button>
          </div>
          <NavContent pathname={pathname} onNavigate={() => setOpen(false)}/>
        </aside>
      </div>

      {/* Desktop sidebar */}
      <aside className="hidden min-h-screen w-64 shrink-0 border-r border-white/5 bg-[#0d1424] p-5 md:flex md:flex-col">
        <Link href="/" className="mb-8 flex items-center gap-3 text-xl font-bold"><Logo/></Link>
        <NavContent pathname={pathname}/>
      </aside>
    </>
  );
}
