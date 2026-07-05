"use client";

import { useState, useEffect } from "react";
import PatternCard from "../components/PatternCard";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Pattern {
  id: string;
  user_id: string;
  label: string;
  service: string;
  incident_count: number;
  status: string;
  streak_started_at: string | null;
  decommissioned_at: string | null;
}

export default function ResolvedPage() {
  const [resolved, setResolved] = useState<Pattern[]>([]);
  const [active, setActive] = useState<Pattern[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPatterns();
    const intervalId = window.setInterval(() => {
      fetchPatterns(true);
    }, 2500);

    return () => window.clearInterval(intervalId);
  }, []);

  async function fetchPatterns(silent = false) {
    try {
      const [resolvedRes, activeRes] = await Promise.all([
        fetch(`${API_URL}/services?status=decommissioned`),
        fetch(`${API_URL}/services?status=active`),
      ]);

      if (resolvedRes.ok) setResolved(await resolvedRes.json());
      if (activeRes.ok) setActive(await activeRes.json());
    } catch (e) {
      console.error("Failed to fetch patterns:", e);
    } finally {
      if (!silent) setLoading(false);
    }
  }

  const totalBroken = resolved.length;
  const totalInstances = resolved.reduce((sum, p) => sum + p.incident_count, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-zinc-400 flex items-center gap-2">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Loading decommissioned services...
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-zinc-100">
          🪦 Decommissioned Services & Handled Precedents
        </h1>
        <p className="text-zinc-500">
          Resolved issues. Post-mortems filed. Architecture improved.
        </p>
      </div>

      {/* Stats bar */}
      {totalBroken > 0 && (
        <div className="glass rounded-xl p-4 flex items-center justify-around animate-fade-in-up">
          <div className="text-center">
            <div className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-green-400 bg-clip-text text-transparent">
              {totalBroken}
            </div>
            <div className="text-xs text-zinc-500 uppercase tracking-wider">Precedents Resolved</div>
          </div>
          <div className="w-px h-10 bg-zinc-700/50" />
          <div className="text-center">
            <div className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              {totalInstances}
            </div>
            <div className="text-xs text-zinc-500 uppercase tracking-wider">Total Incidents</div>
          </div>
          <div className="w-px h-10 bg-zinc-700/50" />
          <div className="text-center">
            <div className="text-3xl">🛡️</div>
            <div className="text-xs text-zinc-500 uppercase tracking-wider">Reliability Hero</div>
          </div>
        </div>
      )}

      {/* Resolved patterns */}
      {resolved.length > 0 ? (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-zinc-300 flex items-center gap-2">
            <span className="animate-confetti">✨</span> Resolved
          </h2>
          <div className="grid gap-3">
            {resolved.map((pattern, idx) => (
              <div
                key={pattern.id}
                className="animate-fade-in-up"
                style={{ animationDelay: `${idx * 100}ms` }}
              >
                <PatternCard pattern={pattern} isResolved />
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="glass rounded-xl p-12 text-center">
          <div className="text-6xl mb-4">🪦</div>
          <h3 className="text-lg font-semibold text-zinc-300 mb-2">
            No precedents resolved yet
          </h3>
          <p className="text-sm text-zinc-500 max-w-md mx-auto">
            When you solve an architectural issue for real — not just a quick hotfix, but permanently —
            you can resolve the precedent and move on. The alerts fade so old on-call pain
            doesn&apos;t linger.
          </p>
          <p className="text-sm text-zinc-600 mt-4 italic">
            Forgetting a bad architecture is a feature you earn, not a bug to prevent.
          </p>
        </div>
      )}

      {/* Active patterns that could be resolved */}
      {active.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-zinc-300">
            Active Precedents <span className="text-zinc-600 font-normal">({active.length})</span>
          </h2>
          <p className="text-sm text-zinc-500">
            Fix these root causes consistently to earn the right to resolve the precedent.
          </p>
          <div className="grid gap-3 opacity-70">
            {active.map((pattern) => (
              <PatternCard key={pattern.id} pattern={pattern} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
