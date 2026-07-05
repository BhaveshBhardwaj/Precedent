"use client";

import { useState } from "react";
import EntryForm from "./components/EntryForm";
import InterruptModal from "./components/InterruptModal";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LogPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [showInterrupt, setShowInterrupt] = useState(false);
  const [interruptData, setInterruptData] = useState<any>(null);
  const [pendingEntry, setPendingEntry] = useState<any>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (data: {
    symptom: string;
    alert: string;
    service: string;
    severity: string;
  }) => {
    setIsLoading(true);
    setPendingEntry(data);
    setSuccessMessage(null);

    try {
      // Step 1: Check for precedent BEFORE saving
      const checkRes = await fetch(`${API_URL}/check-precedent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symptom: data.symptom,
          alert: data.alert,
          service: data.service,
        }),
      });

      if (checkRes.ok) {
        const interruptResult = await checkRes.json();

        if (interruptResult.precedent_found) {
          // Show the precedent modal!
          setInterruptData(interruptResult);
          setShowInterrupt(true);
          setIsLoading(false);
          return; // Don't save yet — let the engineer decide
        }
      }

      // No precedent found — save directly
      await saveEntry(data);
    } catch (error) {
      console.error("Precedent check failed:", error);
      // If precedent check fails, still save the incident
      await saveEntry(data);
    }
  };

  const saveEntry = async (data: any) => {
    try {
      const res = await fetch(`${API_URL}/incidents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (res.ok) {
        setSuccessMessage("Incident logged. Good luck. 🛠️");
      } else {
        setSuccessMessage("Incident saved locally (Cognee sync pending).");
      }
    } catch (error) {
      setSuccessMessage("Backend not reachable. Start the server first.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogAnyway = async () => {
    setShowInterrupt(false);
    if (pendingEntry) {
      setIsLoading(true);
      await saveEntry(pendingEntry);
    }
  };

  const handleChangedMind = () => {
    setShowInterrupt(false);
    setSuccessMessage("Precedent applied! Time saved. 🎉");
    setPendingEntry(null);
    setIsLoading(false);
  };

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="text-center space-y-3 pt-4">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
          What broke this time?
        </h1>
        <p className="text-zinc-500 text-lg max-w-md mx-auto">
          Log the incident. We&apos;ll check if the team has solved this before.
        </p>
      </div>

      {/* Entry Form */}
      <div className="glass rounded-2xl p-6">
        <EntryForm onSubmit={handleSubmit} isLoading={isLoading} />
      </div>

      {/* Success message */}
      {successMessage && (
        <div className="animate-fade-in-up glass rounded-xl p-4 text-center">
          <p className="text-zinc-300">{successMessage}</p>
        </div>
      )}

      {/* Interrupt Modal */}
      <InterruptModal
        isOpen={showInterrupt}
        onClose={() => setShowInterrupt(false)}
        onLogAnyway={handleLogAnyway}
        onChangedMind={handleChangedMind}
        data={interruptData}
      />
    </div>
  );
}
