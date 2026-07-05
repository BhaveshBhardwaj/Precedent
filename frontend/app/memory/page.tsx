"use client";

import GraphView from "../components/GraphView";

export default function MemoryPage() {
  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-zinc-100">🧠 Memory Graph</h1>
        <p className="text-zinc-500">
          Your on-call memory as a live knowledge graph. Watch precedents form,
          grow, and dissolve.
        </p>
      </div>

      <GraphView />

      <div className="glass rounded-xl p-4">
        <h3 className="text-sm font-semibold text-zinc-400 mb-2">How to read this</h3>
        <ul className="text-xs text-zinc-500 space-y-1">
          <li>• <span className="text-purple-400">Purple nodes</span> are entities extracted from your incidents</li>
          <li>• <span className="text-green-400">Green nodes</span> are NodeSets (user + service scoping)</li>
          <li>• <span className="text-pink-400">Pink nodes</span> are documents (your incidents)</li>
          <li>• <span className="text-amber-400">Amber nodes</span> are temporal events</li>
          <li>• Edges show how Cognee connected your incidents into precedents</li>
          <li>• When you resolve a precedent, watch the related nodes fade from the graph</li>
        </ul>
      </div>
    </div>
  );
}
