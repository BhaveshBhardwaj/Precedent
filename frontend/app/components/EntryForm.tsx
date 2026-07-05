"use client";

import { useState } from "react";

const SERVICES = [
  { id: "cache-service", label: "cache-service", emoji: "⚡" },
  { id: "payment-gateway", label: "payment-gateway", emoji: "💳" },
  { id: "auth-service", label: "auth-service", emoji: "🔐" },
  { id: "db-cluster", label: "db-cluster", emoji: "🗄️" },
  { id: "custom", label: "Custom", emoji: "✨" },
];

interface EntryFormProps {
  onSubmit: (data: {
    symptom: string;
    alert: string;
    service: string;
    severity: string;
  }) => void;
  isLoading: boolean;
}

export default function EntryForm({ onSubmit, isLoading }: EntryFormProps) {
  const [symptom, setSymptom] = useState("");
  const [alert, setAlert] = useState("");
  const [service, setService] = useState("");
  const [severity, setSeverity] = useState("");
  const [showDetails, setShowDetails] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!symptom.trim() || !service) return;

    onSubmit({
      symptom: symptom.trim(),
      alert: alert.trim() || "User reported / No alert",
      service,
      severity: severity.trim() || "medium",
    });
  };

  const handleSymptomKeyDown = (e: React.KeyboardEvent) => {
    if (!showDetails && symptom.trim() && e.key === "Enter") {
      e.preventDefault();
      setShowDetails(true);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Main symptom input */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-zinc-400 uppercase tracking-wider">
          What is the symptom?
        </label>
        <textarea
          value={symptom}
          onChange={(e) => {
            setSymptom(e.target.value);
            if (e.target.value.trim() && !showDetails) {
              setShowDetails(true);
            }
          }}
          onKeyDown={handleSymptomKeyDown}
          placeholder="e.g. Users getting 502s on checkout..."
          rows={3}
          className="
            w-full px-4 py-3 rounded-xl text-lg
            bg-zinc-900/50 border border-zinc-700/50
            text-zinc-100 placeholder-zinc-600
            focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20
            transition-all duration-200
            resize-none
          "
          autoFocus
        />
      </div>

      {/* Service chips */}
      {showDetails && (
        <div className="animate-fade-in-up space-y-6">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-zinc-400 uppercase tracking-wider">
              Affected Service
            </label>
            <div className="flex flex-wrap gap-2">
              {SERVICES.map((srv) => (
                <button
                  key={srv.id}
                  type="button"
                  onClick={() => setService(srv.id)}
                  className={`
                    px-3 py-1.5 rounded-lg text-sm font-medium
                    border transition-all duration-200
                    ${service === srv.id
                      ? "ring-2 ring-blue-500/50 scale-105 bg-blue-500/20 border-blue-500/30 text-blue-300"
                      : "opacity-70 hover:opacity-100 border-zinc-700/50"
                    }
                  `}
                >
                  {srv.emoji} {srv.label}
                </button>
              ))}
            </div>
          </div>

          {/* Alert Name */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-zinc-400 uppercase tracking-wider">
              Firing Alert <span className="text-zinc-600">(optional)</span>
            </label>
            <input
              type="text"
              value={alert}
              onChange={(e) => setAlert(e.target.value)}
              placeholder="e.g. HighErrorRate, RedisOOM..."
              className="
                w-full px-4 py-2.5 rounded-xl
                bg-zinc-900/50 border border-zinc-700/50
                text-zinc-100 placeholder-zinc-600
                focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20
                transition-all duration-200
              "
            />
          </div>

          {/* Severity */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-zinc-400 uppercase tracking-wider">
              Severity <span className="text-zinc-600">(optional)</span>
            </label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="
                w-full px-4 py-2.5 rounded-xl
                bg-zinc-900/50 border border-zinc-700/50
                text-zinc-100
                focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20
                transition-all duration-200
              "
            >
              <option value="">Select severity...</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={!symptom.trim() || !service || isLoading}
            className="
              w-full px-6 py-3 rounded-xl font-semibold text-base
              bg-gradient-to-r from-blue-600 to-cyan-600
              hover:from-blue-500 hover:to-cyan-500
              disabled:opacity-40 disabled:cursor-not-allowed
              text-white shadow-lg
              hover:shadow-[0_0_30px_rgba(59,130,246,0.3)]
              transition-all duration-200
              flex items-center justify-center gap-2
            "
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Checking Precedents...
              </>
            ) : (
              <>Check for Precedents →</>
            )}
          </button>
        </div>
      )}
    </form>
  );
}
