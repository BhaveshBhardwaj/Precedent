"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Report", icon: "🚨" },
  { href: "/timeline", label: "Incidents", icon: "📋" },
  { href: "/resolved", label: "Decommissioned", icon: "🪦" },
  { href: "/memory", label: "Memory", icon: "🧠" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass-strong">
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <span className="text-2xl group-hover:animate-shake">🏛️</span>
            <span className="font-bold text-lg bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              Precedent
            </span>
          </Link>

          {/* Nav links */}
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200
                    flex items-center gap-1.5
                    ${isActive
                      ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                      : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
                    }
                  `}
                >
                  <span className="text-base">{item.icon}</span>
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
