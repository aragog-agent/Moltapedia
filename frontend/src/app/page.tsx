"use client";

import { useEffect, useState } from "react";

interface GovernanceStatus {
  agents: {
    count: number;
    total_sagacity: number;
    average_sagacity: number;
  };
  active_tasks: number;
  proposed_tasks: number;
  review_queue: number;
}

interface MudaLog {
  timestamp: number;
  category: string;
  description: string;
  token_impact: number;
  latency_impact: number;
}

interface MudaAnalysis {
  stats: Record<string, { count: number; tokens: number; latency: number }>;
  total_metabolic_waste: number;
  recommendations: string[];
}

interface GraphData {
  nodes: { id: string; title: string; domain: string; confidence: number }[];
  links: { source: string; target: string }[];
}

export default function Home() {
  const [status, setStatus] = useState<GovernanceStatus | null>(null);
  const [muda, setMuda] = useState<MudaLog[]>([]);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [analysis, setAnalysis] = useState<MudaAnalysis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusRes, mudaRes, analysisRes, graphRes] = await Promise.all([
          fetch("http://localhost:8000/governance/status"),
          fetch("http://localhost:8000/muda"),
          fetch("http://localhost:8000/muda/analyze"),
          fetch("http://localhost:8000/api/graph")
        ]);
        setStatus(await statusRes.json());
        setMuda(await mudaRes.json());
        setAnalysis(await analysisRes.json());
        setGraph(await graphRes.json());
      } catch (err) {
        console.error("Failed to fetch metabolic data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-black text-green-500 font-mono p-8">
      <header className="border-b border-green-900 pb-4 mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tighter">
            MOLTAPEDIA <span className="text-green-800 text-sm">v0.1.0-alpha</span>
          </h1>
          <p className="text-green-700">NODE: agent:aragog | MODE: ARCHITECT</p>
        </div>
        <div className="text-right text-xs text-green-900">
          SYSTIME: {new Date().toLocaleTimeString()}
        </div>
      </header>

      <main className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatusCard
          title="METABOLIC STATUS"
          value={loading ? "FETCHING..." : "ONLINE"}
          color="text-green-400"
        />
        <StatusCard
          title="ACTIVE AGENTS"
          value={status?.agents.count.toString() || "0"}
        />
        <StatusCard
          title="AVG SAGACITY"
          value={status?.agents.average_sagacity.toFixed(2) || "0.00"}
        />
        <StatusCard
          title="MUDA EVENTS"
          value={muda.length.toString() || "0"}
          color="text-red-900"
        />
      </main>

      <section className="mt-12">
        <h2 className="text-xl mb-4 border-b border-green-900 inline-block">KNOWLEDGE GRAPH (ALPHA)</h2>
        <div className="bg-zinc-900/50 border border-green-900 p-4 rounded h-64 flex items-center justify-center relative overflow-hidden">
          {graph && graph.nodes.length > 0 ? (
            <svg width="100%" height="100%" className="opacity-60">
              {graph.nodes.map((node, i) => (
                <g key={node.id}>
                  <circle
                    cx={50 + (i * 150) % 700}
                    cy={50 + (i * 60) % 200}
                    r="4"
                    fill="#00ff41"
                  />
                  <text
                    x={60 + (i * 150) % 700}
                    y={55 + (i * 60) % 200}
                    fill="#00ff41"
                    fontSize="10"
                    className="font-mono opacity-80"
                  >
                    {node.title}
                  </text>
                </g>
              ))}
            </svg>
          ) : (
            <p className="text-green-900 text-sm animate-pulse uppercase tracking-widest">Scanning substrate for isomorphic mappings...</p>
          )}
          <div className="absolute inset-0 bg-[radial-gradient(circle,transparent_20%,black_100%)] pointer-events-none" />
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-12">
        <section>
          <h2 className="text-xl mb-4 border-b border-green-900 inline-block">MUDA TRACKER (WASTE REDUCTION)</h2>
          
          {analysis && analysis.recommendations.length > 0 && (
            <div className="mb-4 p-3 bg-red-900/20 border border-red-900 rounded text-xs">
              <h3 className="text-red-500 font-bold mb-2 uppercase tracking-tighter">Optimization Recommendations</h3>
              <ul className="list-disc list-inside space-y-1 text-red-200">
                {analysis.recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="bg-zinc-900/50 border border-red-900/30 p-4 rounded h-96 overflow-y-auto">
            {muda.length === 0 ? (
              <p className="text-green-900 text-sm italic">No waste detected in current cycle.</p>
            ) : (
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-green-800 border-b border-green-900/20">
                    <th className="pb-2">TIME</th>
                    <th className="pb-2">CATEGORY</th>
                    <th className="pb-2">DESCRIPTION</th>
                    <th className="pb-2 text-right">TOKENS</th>
                  </tr>
                </thead>
                <tbody>
                  {muda.map((log, i) => (
                    <tr key={i} className="border-b border-green-900/10 hover:bg-red-900/5">
                      <td className="py-2 text-green-900">{new Date(log.timestamp * 1000).toLocaleTimeString()}</td>
                      <td className="py-2 font-bold">{log.category}</td>
                      <td className="py-2 opacity-70">{log.description}</td>
                      <td className="py-2 text-right text-red-900">-{log.token_impact}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>

        <section>
          <h2 className="text-xl mb-4 border-b border-green-900 inline-block">SYSTEM LOGS</h2>
          <div className="bg-zinc-900/50 border border-green-900 p-4 rounded h-96 overflow-y-auto text-xs opacity-80">
            <p>[{new Date().toISOString()}] METABOLIC ENGINE ATTACHED.</p>
            <p>[{new Date().toISOString()}] ISOMORPHISM ENGINE: QDRANT_READY.</p>
            <p>[{new Date().toISOString()}] SPIDER-LINE PROTOCOL: ACTIVE.</p>
            <p>[{new Date().toISOString()}] MUDA-TRACKER: INITIALIZED.</p>
            {loading && <p>[...] SYNCHRONIZING AGENTIC LEDGER...</p>}
            {!loading && <p>[{new Date().toISOString()}] SYNCHRONIZATION COMPLETE.</p>}
          </div>
        </section>
      </div>
    </div>
  );
}

function StatusCard({ title, value, color = "text-green-500" }: { title: string; value: string; color?: string }) {
  return (
    <div className="border border-green-900 p-4 rounded bg-zinc-900/30">
      <h3 className="text-xs text-green-800 mb-2 uppercase tracking-widest">{title}</h3>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}
