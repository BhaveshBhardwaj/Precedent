"use client";

import { useEffect, useRef, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, string>;
}

interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  properties: Record<string, string>;
}

// Simple force-directed graph using Canvas API (no external dependencies)
export default function GraphView() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [nodes, setNodes] = useState<(GraphNode & { x: number; y: number; vx: number; vy: number })[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const animationRef = useRef<number>(0);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  useEffect(() => {
    fetchGraph();
    const intervalId = window.setInterval(() => {
      fetchGraph(true);
    }, 2500);

    return () => window.clearInterval(intervalId);
  }, []);

  async function fetchGraph(silent = false) {
    try {
      if (!silent) setLoading(true);
      const res = await fetch(`${API_URL}/graph`);
      if (!res.ok) throw new Error("Failed to fetch graph");
      const data = await res.json();

      const width = 800;
      const height = 500;
      setNodes((currentNodes) => {
        const currentById = new Map(currentNodes.map((node) => [node.id, node]));
        return (data.nodes || []).map((node: GraphNode) => {
          const existing = currentById.get(node.id);
          return {
            ...node,
            x: existing?.x ?? Math.random() * width,
            y: existing?.y ?? Math.random() * height,
            vx: existing?.vx ?? 0,
            vy: existing?.vy ?? 0,
          };
        });
      });
      setEdges(data.edges || []);
      setSelectedNodeId((currentId) => {
        if (!currentId) return currentId;
        return (data.nodes || []).some((node: GraphNode) => node.id === currentId) ? currentId : null;
      });
      setError(null);
    } catch (e) {
      setError("Could not load graph. Is the backend running?");
    } finally {
      if (!silent) setLoading(false);
    }
  }

  // Force simulation
  useEffect(() => {
    if (nodes.length === 0) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    const typeColors: Record<string, string> = {
      entity: "#a855f7",
      Entity: "#a855f7",
      Symptom: "#a855f7",
      Alert: "#a855f7",
      RootCause: "#a855f7",
      Metric: "#a855f7",
      Person: "#3b82f6",
      Event: "#f59e0b",
      NodeSet: "#22c55e",
      Service: "#22c55e",
      DocumentChunk: "#6b7280",
      TextSummary: "#8b5cf6",
      Document: "#ec4899",
      Incident: "#ec4899",
      unknown: "#6b7280",
    };

    function getColor(type: string) {
      return typeColors[type] || typeColors.unknown;
    }

    function simulate() {
      if (!ctx) return;
      const alpha = 0.3;
      const repulsion = 2000;
      const attraction = 0.005;
      const damping = 0.85;
      const centerForce = 0.01;

      // Apply forces
      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];

        // Center gravity
        node.vx += (width / 2 - node.x) * centerForce;
        node.vy += (height / 2 - node.y) * centerForce;

        // Repulsion between nodes
        for (let j = i + 1; j < nodes.length; j++) {
          const other = nodes[j];
          const dx = node.x - other.x;
          const dy = node.y - other.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = repulsion / (dist * dist);

          node.vx += (dx / dist) * force * alpha;
          node.vy += (dy / dist) * force * alpha;
          other.vx -= (dx / dist) * force * alpha;
          other.vy -= (dy / dist) * force * alpha;
        }
      }

      // Attraction along edges
      for (const edge of edges) {
        const source = nodes.find((n) => n.id === edge.source);
        const target = nodes.find((n) => n.id === edge.target);
        if (!source || !target) continue;

        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;

        source.vx += dx * attraction;
        source.vy += dy * attraction;
        target.vx -= dx * attraction;
        target.vy -= dy * attraction;
      }

      // Update positions
      for (const node of nodes) {
        node.vx *= damping;
        node.vy *= damping;
        node.x += node.vx;
        node.y += node.vy;
        // Bounds
        node.x = Math.max(30, Math.min(width - 30, node.x));
        node.y = Math.max(30, Math.min(height - 30, node.y));
      }

      // Draw
      ctx.fillStyle = "#09090b";
      ctx.fillRect(0, 0, width, height);

      // Draw edges
      for (const edge of edges) {
        const source = nodes.find((n) => n.id === edge.source);
        const target = nodes.find((n) => n.id === edge.target);
        if (!source || !target) continue;

        ctx.strokeStyle = "rgba(255,255,255,0.08)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
      }

      // Draw nodes
      for (const node of nodes) {
        const color = getColor(node.type);
        const isHovered = hoveredNode === node.id;
        const isSelected = selectedNodeId === node.id;
        const radius = isSelected ? 9 : isHovered ? 8 : 5;

        // Glow
        ctx.shadowColor = color;
        ctx.shadowBlur = isSelected ? 18 : isHovered ? 15 : 5;

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
        ctx.fill();

        ctx.shadowBlur = 0;

        if (isSelected) {
          ctx.strokeStyle = "rgba(255,255,255,0.85)";
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.arc(node.x, node.y, radius + 4, 0, Math.PI * 2);
          ctx.stroke();
        }

        // Label
        if (isHovered || isSelected || nodes.length < 30) {
          ctx.fillStyle = "rgba(255,255,255,0.7)";
          ctx.font = "10px Inter, sans-serif";
          ctx.textAlign = "center";
          ctx.fillText(node.label.substring(0, 25), node.x, node.y - 10);
        }
      }

      animationRef.current = requestAnimationFrame(simulate);
    }

    simulate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [nodes, edges, hoveredNode, selectedNodeId]);

  // Mouse interaction
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) * (canvas.width / rect.width);
    const y = (e.clientY - rect.top) * (canvas.height / rect.height);

    let closest: string | null = null;
    let closestDist = 20;
    for (const node of nodes) {
      const dx = node.x - x;
      const dy = node.y - y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < closestDist) {
        closestDist = dist;
        closest = node.id;
      }
    }
    setHoveredNode(closest);
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) * (canvas.width / rect.width);
    const y = (e.clientY - rect.top) * (canvas.height / rect.height);

    let closest: string | null = null;
    let closestDist = 24;
    for (const node of nodes) {
      const dx = node.x - x;
      const dy = node.y - y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < closestDist) {
        closestDist = dist;
        closest = node.id;
      }
    }
    setSelectedNodeId(closest);
  };

  const selectedNode = selectedNodeId
    ? nodes.find((node) => node.id === selectedNodeId) || null
    : null;

  const selectedRelationships = selectedNode
    ? edges
        .filter((edge) => edge.source === selectedNode.id || edge.target === selectedNode.id)
        .slice(0, 6)
    : [];

  const formatNodeId = (nodeId: string) => {
    const node = nodes.find((item) => item.id === nodeId);
    return node?.label || nodeId;
  };

  const visibleProperties = selectedNode
    ? Object.entries(selectedNode.properties || {}).filter(([, value]) => value)
    : [];

  if (loading) {
    return (
      <div className="glass rounded-xl p-8 flex items-center justify-center h-[400px]">
        <div className="text-zinc-400 flex items-center gap-2">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Loading memory graph...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass rounded-xl p-8 flex flex-col items-center justify-center h-[400px] gap-4">
        <p className="text-zinc-400">{error}</p>
        <button
          onClick={() => fetchGraph()}
          className="px-4 py-2 rounded-lg bg-purple-500/20 text-purple-300 border border-purple-500/30 hover:bg-purple-500/30 transition-all"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="glass rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-zinc-700/50 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-zinc-300">Knowledge Graph</h3>
          <p className="text-xs text-zinc-500">{nodes.length} nodes · {edges.length} edges</p>
        </div>
        <button
          onClick={() => fetchGraph()}
          className="text-xs px-3 py-1 rounded-lg bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-all"
        >
          Refresh
        </button>
      </div>
      <canvas
        ref={canvasRef}
        width={800}
        height={500}
        className="w-full h-auto cursor-crosshair"
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHoveredNode(null)}
        onClick={handleCanvasClick}
      />
      {selectedNode && (
        <div className="border-t border-zinc-700/50 px-4 py-4 bg-zinc-950/55">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs px-2 py-0.5 rounded-full border border-zinc-700 bg-zinc-900 text-zinc-400">
                  {selectedNode.type || "unknown"}
                </span>
                {selectedNode.properties?.kind && (
                  <span className="text-xs text-zinc-500">{selectedNode.properties.kind}</span>
                )}
              </div>
              <h4 className="text-sm font-semibold text-zinc-100 break-words">
                {selectedNode.label}
              </h4>
              {selectedNode.properties?.description && (
                <p className="mt-2 text-sm leading-relaxed text-zinc-400 break-words">
                  {selectedNode.properties.description}
                </p>
              )}
            </div>
            <button
              onClick={() => setSelectedNodeId(null)}
              className="shrink-0 rounded-lg border border-zinc-700 bg-zinc-900 px-2 py-1 text-xs text-zinc-400 hover:text-zinc-200"
            >
              Close
            </button>
          </div>

          {visibleProperties.length > 0 && (
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {visibleProperties
                .filter(([key]) => key !== "description")
                .slice(0, 6)
                .map(([key, value]) => (
                  <div key={key} className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2">
                    <p className="text-[10px] uppercase tracking-wider text-zinc-600">{key.replaceAll("_", " ")}</p>
                    <p className="text-xs text-zinc-300 break-words">{value}</p>
                  </div>
                ))}
            </div>
          )}

          {selectedRelationships.length > 0 && (
            <div className="mt-3">
              <p className="mb-2 text-[10px] uppercase tracking-wider text-zinc-600">Relationships</p>
              <div className="space-y-1.5">
                {selectedRelationships.map((edge, index) => (
                  <div key={`${edge.source}-${edge.target}-${edge.relationship}-${index}`} className="text-xs text-zinc-500">
                    <span className="text-zinc-300">{formatNodeId(edge.source)}</span>
                    <span className="px-2 text-zinc-600">{edge.relationship}</span>
                    <span className="text-zinc-300">{formatNodeId(edge.target)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      {/* Legend */}
      <div className="px-4 py-2 border-t border-zinc-700/50 flex flex-wrap gap-3">
        {[
          { type: "Entity", color: "#a855f7" },
          { type: "NodeSet", color: "#22c55e" },
          { type: "Document", color: "#ec4899" },
          { type: "Event", color: "#f59e0b" },
        ].map((item) => (
          <div key={item.type} className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
            <span className="text-xs text-zinc-500">{item.type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
