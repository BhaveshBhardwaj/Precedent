"use client";

import { useState, useEffect } from "react";

interface InterruptModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLogAnyway: () => void;
  onChangedMind: () => void;
  data: {
    precedent_found: boolean;
    match_count: number;
    confidence: string;
    past_incidents: string[];
    message: string;
  } | null;
}

export default function InterruptModal({
  isOpen,
  onClose,
  onLogAnyway,
  onChangedMind,
  data,
}: InterruptModalProps) {
  const [isAnimating, setIsAnimating] = useState(false);
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    if (isOpen && data?.precedent_found) {
      setIsAnimating(true);
      // Shake first, then reveal content
      setTimeout(() => {
        setShowContent(true);
      }, 600);
    } else {
      setIsAnimating(false);
      setShowContent(false);
    }
  }, [isOpen, data]);

  if (!isOpen || !data?.precedent_found) return null;

  const confidenceColors: Record<string, string> = {
    emerging: "from-yellow-500 to-amber-500",
    recurring: "from-orange-500 to-red-500",
    deep_loop: "from-red-500 to-rose-600",
  };

  const confidenceLabels: Record<string, string> = {
    emerging: "Emerging Precedent",
    recurring: "Recurring Incident",
    deep_loop: "Deep Precedent",
  };

  const gradientClass = confidenceColors[data.confidence] || confidenceColors.emerging;
  const label = confidenceLabels[data.confidence] || "Precedent Detected";

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm animate-fade-in-up"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={`
          relative w-full max-w-lg glass-strong rounded-2xl overflow-hidden
          ${isAnimating ? "animate-shake" : ""}
          ${showContent ? "animate-fade-in-up" : ""}
        `}
      >
        {/* Top danger bar */}
        <div className={`h-1.5 bg-gradient-to-r ${gradientClass}`} />

        {/* Header */}
        <div className="px-6 pt-6 pb-4">
          <div className="flex items-center gap-3 mb-4">
            <div
              className={`
                w-12 h-12 rounded-full flex items-center justify-center text-2xl
                bg-gradient-to-br ${gradientClass} animate-pulse-glow
              `}
            >
              {data.confidence === "deep_loop" ? "🚨" : data.confidence === "recurring" ? "⚠️" : "👀"}
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">{label}</h2>
              <p className="text-sm text-zinc-400">
                {data.match_count} similar incident{data.match_count !== 1 ? "s" : ""} found
              </p>
            </div>
          </div>

          <p className="text-zinc-300 text-base leading-relaxed">
            {data.message}
          </p>
        </div>

        {/* Past instances */}
        {showContent && data.past_incidents.length > 0 && (
          <div className="px-6 pb-4">
            <div className="bg-zinc-900/60 rounded-xl p-4 border border-zinc-700/50 max-h-64 overflow-y-auto">
              <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
                Historical Root Causes
              </h3>
              {data.past_incidents.map((instance, i) => (
                <div
                  key={i}
                  className="animate-slide-in mb-3 last:mb-0"
                  style={{ animationDelay: `${i * 100}ms` }}
                >
                  <div className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">
                    {instance}
                  </div>
                  {i < data.past_incidents.length - 1 && (
                    <div className="border-b border-zinc-700/30 mt-3" />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="px-6 pb-6 flex gap-3">
          <button
            onClick={onChangedMind}
            className="
              flex-1 px-4 py-3 rounded-xl font-semibold text-sm
              bg-emerald-500/20 text-emerald-300 border border-emerald-500/30
              hover:bg-emerald-500/30 hover:border-emerald-500/50
              transition-all duration-200
              hover:shadow-[0_0_20px_rgba(34,197,94,0.2)]
            "
          >
            ✋ Apply Precedent
          </button>
          <button
            onClick={onLogAnyway}
            className="
              flex-1 px-4 py-3 rounded-xl font-semibold text-sm
              bg-red-500/20 text-red-300 border border-red-500/30
              hover:bg-red-500/30 hover:border-red-500/50
              transition-all duration-200
              hover:shadow-[0_0_20px_rgba(239,68,68,0.2)]
            "
          >
            Log novel incident →
          </button>
        </div>
      </div>
    </div>
  );
}
