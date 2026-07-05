"use client";

interface PatternCardProps {
  pattern: {
    id: string;
    label: string;
    service: string;
    incident_count: number;
    status: string;
    streak_started_at?: string | null;
    decommissioned_at?: string | null;
  };
  onResolve?: (id: string) => void;
  isResolved?: boolean;
}

const serviceEmojis: Record<string, string> = {
  "cache-service": "⚡",
  "payment-gateway": "💳",
  "auth-service": "🔐",
  "db-cluster": "🗄️",
  custom: "✨",
};

const serviceColors: Record<string, string> = {
  "cache-service": "from-blue-500/20 to-blue-600/10 border-blue-500/20",
  "payment-gateway": "from-emerald-500/20 to-emerald-600/10 border-emerald-500/20",
  "auth-service": "from-purple-500/20 to-purple-600/10 border-purple-500/20",
  "db-cluster": "from-orange-500/20 to-orange-600/10 border-orange-500/20",
  custom: "from-zinc-500/20 to-zinc-600/10 border-zinc-500/20",
};

export default function PatternCard({ pattern, onResolve, isResolved }: PatternCardProps) {
  const emoji = serviceEmojis[pattern.service] || "📌";
  const colorClass = serviceColors[pattern.service] || serviceColors.custom;

  const getStrength = (count: number) => {
    if (count >= 6) return { label: "Deep Precedent", color: "text-red-400", bar: "bg-red-500" };
    if (count >= 4) return { label: "Recurring Issue", color: "text-orange-400", bar: "bg-orange-500" };
    if (count >= 2) return { label: "Emerging Pattern", color: "text-yellow-400", bar: "bg-yellow-500" };
    return { label: "New", color: "text-zinc-400", bar: "bg-zinc-500" };
  };

  const strength = getStrength(pattern.incident_count);

  return (
    <div
      className={`
        rounded-xl border bg-gradient-to-br ${colorClass}
        p-4 transition-all duration-300
        ${isResolved ? "opacity-60" : "hover:scale-[1.01] hover:border-opacity-40"}
      `}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{isResolved ? "🛠️" : emoji}</span>
          <div>
            <h3 className="font-semibold text-zinc-100">{pattern.label}</h3>
            <span className={`text-xs font-medium ${strength.color}`}>
              {isResolved ? "✅ Precedent Handled" : strength.label}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-zinc-200">{pattern.incident_count}</div>
          <div className="text-xs text-zinc-500">incidents</div>
        </div>
      </div>

      {/* Strength bar */}
      {!isResolved && (
        <div className="mb-3">
          <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className={`h-full ${strength.bar} rounded-full transition-all duration-500`}
              style={{ width: `${Math.min(pattern.incident_count * 15, 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Category badge */}
      <div className="flex items-center justify-between">
        <span className="text-xs px-2 py-0.5 rounded-full border border-zinc-700 bg-zinc-800 text-zinc-300">
          {pattern.service}
        </span>

        {!isResolved && onResolve && pattern.incident_count >= 2 && (
          <button
            onClick={() => onResolve(pattern.id)}
            className="
              text-xs px-3 py-1 rounded-lg
              bg-emerald-500/10 text-emerald-400 border border-emerald-500/20
              hover:bg-emerald-500/20 transition-all duration-200
            "
          >
            Decommission / Resolve ✨
          </button>
        )}

        {isResolved && pattern.decommissioned_at && (
          <span className="text-xs text-zinc-500">
            Resolved {new Date(pattern.decommissioned_at).toLocaleDateString()}
          </span>
        )}
      </div>
    </div>
  );
}
