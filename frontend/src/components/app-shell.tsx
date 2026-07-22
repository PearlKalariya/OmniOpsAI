"use client";

/** Nav + auth gate. Unauthenticated users only ever see the login card. */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { LoginCard } from "@/components/login-card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard" },
  { href: "/documents", label: "Documents" },
  { href: "/chat", label: "Chat" },
  { href: "/evaluation", label: "Evaluation" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const { authed, ready, logout } = useAuth();
  const pathname = usePathname();

  if (!ready) {
    return (
      <div className="flex-1 grid place-items-center text-sm text-muted-foreground">
        Loading…
      </div>
    );
  }

  if (!authed) {
    return (
      <div className="flex-1 grid place-items-center p-6">
        <LoginCard />
      </div>
    );
  }

  return (
    <>
      <header className="border-b">
        <div className="mx-auto max-w-6xl flex items-center gap-6 px-6 h-14">
          <Link href="/" className="font-semibold tracking-tight">
            OmniOps <span className="text-primary">AI</span>
          </Link>
          <nav className="flex gap-1 flex-1">
            {NAV.map((n) => (
              <Link
                key={n.href}
                href={n.href}
                className={cn(
                  "px-3 py-1.5 text-sm rounded-md transition-colors",
                  pathname === n.href
                    ? "bg-secondary text-secondary-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {n.label}
              </Link>
            ))}
          </nav>
          <Button variant="ghost" size="sm" onClick={logout}>
            Log out
          </Button>
        </div>
      </header>
      <main className="flex-1 mx-auto w-full max-w-6xl p-6">{children}</main>
    </>
  );
}
