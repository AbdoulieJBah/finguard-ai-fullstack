"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "./Sidebar";
import { useAuth } from "./AuthProvider";

/** Page frame for signed-in screens: sidebar, sign-in check and optional role check. */
export default function AppShell({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { user, ready } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (ready && !user) router.replace("/login");
  }, [ready, user, router]);

  let content: React.ReactNode = children;
  if (!ready || !user) {
    content = <p className="text-slate-400">Checking your session…</p>;
  } else if (roles && !roles.includes(user.role)) {
    content = (
      <div className="rounded-2xl border border-amber-400/20 bg-amber-400/5 p-6 text-amber-200">
        This page is not available to the {user.role} role.
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-[#0B1120] text-white md:flex-row">
      <Sidebar />
      <main className="min-w-0 flex-1 p-4 sm:p-6 lg:p-8">{content}</main>
    </div>
  );
}

export function ErrorNotice({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-400/20 bg-red-500/10 p-4 text-sm text-red-200">
      <span>{message}</span>
      {onRetry && (
        <button type="button" onClick={onRetry} className="rounded-lg border border-red-300/30 px-3 py-1.5 font-semibold hover:bg-red-400/10">
          Try again
        </button>
      )}
    </div>
  );
}

export function PageHeader({ eyebrow, title, description }: { eyebrow?: string; title: string; description?: string }) {
  return (
    <header>
      {eyebrow && <p className="text-xs uppercase tracking-[0.25em] text-cyan-400">{eyebrow}</p>}
      <h1 className="mt-2 text-3xl font-bold sm:text-4xl lg:text-5xl">{title}</h1>
      {description && <p className="mt-3 max-w-3xl text-slate-400">{description}</p>}
    </header>
  );
}
