"use client";

import { useState, useEffect } from "react";
import PatternCard from "../components/PatternCard";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Incident {
  id: string;
  user_id: string;
  symptom: string;
  alert: string;
  service: string;
  severity: string | null;
  created_at: string;
  root_cause_and_fix: string | null;
  root_cause_logged_at: string | null;
}

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

const serviceEmojis: Record<string, string> = {
  "cache-service": "⚡",
  "payment-gateway": "💳",
  "auth-service": "🔐",
  "db-cluster": "🗄️",
  custom: "✨",
};

export default function TimelinePage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [loading, setLoading] = useState(true);
  const [outcomeModal, setOutcomeModal] = useState<string | null>(null);
  const [outcomeText, setOutcomeText] = useState("");
  const [savingOutcome, setSavingOutcome] = useState(false);

  useEffect(() => {
    fetchData();
    const intervalId = window.setInterval(() => {
      fetchData(true);
    }, 2500);

    return () => window.clearInterval(intervalId);
  }, []);

  async function fetchData(silent = false) {
    try {
      const [incidentsRes, patternsRes] = await Promise.all([
        fetch(`${API_URL}/incidents`),
        fetch(`${API_URL}/services?status=active`),
      ]);

      if (incidentsRes.ok) setIncidents(await incidentsRes.json());
      if (patternsRes.ok) setPatterns(await patternsRes.json());
    } catch (e) {
      console.error("Failed to fetch data:", e);
    } finally {
      if (!silent) setLoading(false);
    }
  }

  async function handleResolve(patternId: string) {
    try {
      const res = await fetch(`${API_URL}/services/${patternId}/decommission`, {
        method: "POST",
      });
      if (res.ok) {
        const resolvedPattern = await res.json();
        setPatterns((current) => current.filter((pattern) => pattern.service !== resolvedPattern.service));
        setIncidents((current) => current.filter((incident) => incident.service !== resolvedPattern.service));
        fetchData(true);
      }
    } catch (e) {
      console.error("Failed to resolve pattern:", e);
    }
  }

  async function handleSaveOutcome(incidentId: string) {
    if (!outcomeText.trim()) return;
    setSavingOutcome(true);
    try {
      const res = await fetch(`${API_URL}/incidents/${incidentId}/root_cause`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ root_cause_and_fix: outcomeText.trim() }),
      });
      if (res.ok) {
        setOutcomeModal(null);
        setOutcomeText("");
        fetchData();
      }
    } catch (e) {
      console.error("Failed to save outcome:", e);
    } finally {
      setSavingOutcome(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-zinc-400 flex items-center gap-2">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Loading incidents...
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-zinc-100">Incident Timeline</h1>
        <p className="text-zinc-500">Your on-call history. Close loops. Prevent regressions.</p>
      </div>

      {/* Active Patterns */}
      {patterns.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-zinc-300">Active Precedents</h2>
          <div className="grid gap-3">
            {patterns.map((pattern) => (
              <PatternCard
                key={pattern.id}
                pattern={pattern}
                onResolve={handleResolve}
              />
            ))}
          </div>
        </div>
      )}

      {/* Incidents Timeline */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-zinc-300">
          All Incidents <span className="text-zinc-600 font-normal">({incidents.length})</span>
        </h2>

        {incidents.length === 0 ? (
          <div className="glass rounded-xl p-8 text-center">
            <p className="text-zinc-500">No incidents yet. On-call is quiet.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {incidents.map((incident, idx) => (
              <div
                key={incident.id}
                className="glass rounded-xl p-4 animate-slide-in"
                style={{ animationDelay: `${Math.min(idx * 50, 500)}ms` }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">
                      {serviceEmojis[incident.service] || "📌"}
                    </span>
                    <div>
                      <p className="font-medium text-zinc-200">{incident.symptom}</p>
                      <p className="text-xs text-zinc-500">
                        {new Date(incident.created_at).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs px-2 py-0.5 rounded-full border border-zinc-700 bg-zinc-800 text-zinc-300">
                    {incident.service}
                  </span>
                </div>

                {incident.alert && incident.alert !== "User reported / No alert" && (
                  <p className="text-sm text-zinc-500 mb-2">
                    <span className="text-zinc-600">Alert:</span> {incident.alert}
                  </p>
                )}

                {incident.severity && (
                  <p className="text-sm text-zinc-500 mb-2">
                    <span className="text-zinc-600">Severity:</span> <span className="uppercase text-xs">{incident.severity}</span>
                  </p>
                )}

                {incident.root_cause_and_fix ? (
                  <div className="mt-2 p-2 rounded-lg bg-zinc-800/50 border border-zinc-700/30">
                    <p className="text-xs text-zinc-600 uppercase tracking-wider mb-1">Root Cause & Fix</p>
                    <p className="text-sm text-zinc-300">{incident.root_cause_and_fix}</p>
                  </div>
                ) : (
                  <button
                    onClick={() => {
                      setOutcomeModal(incident.id);
                      setOutcomeText("");
                    }}
                    className="
                      mt-2 text-xs px-3 py-1.5 rounded-lg
                      bg-amber-500/10 text-amber-400 border border-amber-500/20
                      hover:bg-amber-500/20 transition-all
                    "
                  >
                    + Close the loop — file post-mortem
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Outcome Modal */}
      {outcomeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setOutcomeModal(null)} />
          <div className="relative glass-strong rounded-2xl p-6 w-full max-w-md animate-fade-in-up">
            <h3 className="text-lg font-semibold text-zinc-100 mb-2">What was the root cause?</h3>
            <p className="text-sm text-zinc-500 mb-4">Close the loop — document how this was resolved so the team has precedent.</p>
            <textarea
              value={outcomeText}
              onChange={(e) => setOutcomeText(e.target.value)}
              placeholder="e.g., Cache eviction failed. Added 5s TTL..."
              rows={3}
              className="
                w-full px-4 py-3 rounded-xl
                bg-zinc-900/50 border border-zinc-700/50
                text-zinc-100 placeholder-zinc-600
                focus:outline-none focus:blue-500/50
                resize-none mb-4
              "
              autoFocus
            />
            <div className="flex gap-3">
              <button
                onClick={() => setOutcomeModal(null)}
                className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium bg-zinc-800 text-zinc-400 hover:bg-zinc-700 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={() => handleSaveOutcome(outcomeModal)}
                disabled={!outcomeText.trim() || savingOutcome}
                className="
                  flex-1 px-4 py-2.5 rounded-xl text-sm font-medium
                  bg-gradient-to-r from-blue-600 to-cyan-600
                  hover:from-blue-500 hover:to-cyan-500
                  disabled:opacity-40 text-white transition-all
                "
              >
                {savingOutcome ? "Saving..." : "Save Root Cause"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
