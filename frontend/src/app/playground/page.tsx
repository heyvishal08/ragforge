"use client";

import { useState, useEffect } from "react";
import { Search, Database, Clock, BarChart3, Zap, ArrowRight, Sliders, Layers } from "lucide-react";
import api from "@/lib/api";
import type { KnowledgeBase, RetrievalResult, RetrievalResponse } from "@/types";
import { formatLatency } from "@/lib/utils";

const strategies = [
  { id: "vector", label: "Vector Search", desc: "pgvector Cosine Distance" },
  { id: "keyword", label: "Keyword Search", desc: "PostgreSQL tsvector BM25" },
  { id: "hybrid", label: "Hybrid RRF + Rerank", desc: "Reciprocal Rank Fusion + MS MARCO" },
];

export default function PlaygroundPage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKb, setSelectedKb] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<
    Record<string, { results: RetrievalResult[]; metadata: Record<string, unknown> }>
  >({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>(["vector", "hybrid"]);

  useEffect(() => {
    api.get<KnowledgeBase[]>("/knowledge-bases").then((data) => {
      setKnowledgeBases(data);
      if (data.length > 0) setSelectedKb(data[0].id);
    });
  }, []);

  const runSearch = async () => {
    if (!query.trim() || !selectedKb) return;

    for (const strategy of selectedStrategies) {
      setLoading((prev) => ({ ...prev, [strategy]: true }));
      try {
        const data = await api.post<RetrievalResponse>("/retrieval/search", {
          knowledge_base_id: selectedKb,
          query,
          strategy,
          top_k: 10,
          rerank: strategy === "hybrid",
        });
        setResults((prev) => ({ ...prev, [strategy]: data }));
      } catch (err) {
        console.error(`Search failed for ${strategy}`, err);
      } finally {
        setLoading((prev) => ({ ...prev, [strategy]: false }));
      }
    }
  };

  const toggleStrategy = (s: string) => {
    setSelectedStrategies((prev) =>
      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]
    );
  };

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="pb-2 border-b border-white/[0.06]">
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          Retrieval Playground
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Perform side-by-side search diagnostics across Dense Vector, Sparse BM25, and Hybrid RRF pipelines.
        </p>
      </div>

      {/* Query Search Card */}
      <div className="glass-panel p-6 rounded-2xl border border-white/[0.06] bg-[#141724]/70 space-y-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <select
            value={selectedKb}
            onChange={(e) => setSelectedKb(e.target.value)}
            className="sm:w-64 px-4 py-2.5 rounded-xl text-sm font-medium bg-[#0e101a] border border-white/[0.08] text-white outline-none focus:border-indigo-500/50"
          >
            <option value="">Select Knowledge Base</option>
            {knowledgeBases.map((kb) => (
              <option key={kb.id} value={kb.id}>
                {kb.name}
              </option>
            ))}
          </select>

          <input
            type="text"
            placeholder="Type a research query to compare retrieval strategies..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && runSearch()}
            className="flex-1 px-4 py-2.5 rounded-xl text-sm bg-[#0e101a] border border-white/[0.08] text-white placeholder:text-slate-500 outline-none focus:border-indigo-500/50"
          />

          <button
            onClick={runSearch}
            disabled={!query.trim() || !selectedKb}
            className="px-6 py-2.5 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 disabled:pointer-events-none text-white shadow-md shadow-indigo-600/20 transition-all flex items-center justify-center gap-2"
          >
            <Search className="w-4 h-4" />
            <span>Compare</span>
          </button>
        </div>

        {/* Strategy Selector Pills */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-white/[0.04]">
          <span className="text-xs font-semibold text-slate-400 mr-2">Active Columns:</span>
          {strategies.map((s) => {
            const isSelected = selectedStrategies.includes(s.id);
            return (
              <button
                key={s.id}
                onClick={() => toggleStrategy(s.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                  isSelected
                    ? "bg-indigo-600/20 text-indigo-300 border-indigo-500/40"
                    : "bg-white/[0.02] text-slate-400 border-white/[0.06] hover:text-slate-200"
                }`}
              >
                {s.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Comparison Grid */}
      <div
        className={`grid gap-6 items-start grid-cols-1 ${
          selectedStrategies.length === 2
            ? "md:grid-cols-2"
            : selectedStrategies.length >= 3
            ? "md:grid-cols-2 xl:grid-cols-3"
            : ""
        }`}
      >
        {selectedStrategies.map((strategyId) => {
          const strat = strategies.find((s) => s.id === strategyId);
          const data = results[strategyId];
          const isLoading = loading[strategyId];

          return (
            <div
              key={strategyId}
              className="glass-panel p-5 rounded-2xl border border-white/[0.06] bg-[#141724]/70 space-y-4"
            >
              <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                <div>
                  <h3 className="text-sm font-bold text-white tracking-tight">{strat?.label}</h3>
                  <div className="text-[11px] text-slate-400">{strat?.desc}</div>
                </div>
                {data?.metadata && (
                  <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                    {formatLatency((data.metadata.retrieval_latency_ms as number) || 0)}
                  </span>
                )}
              </div>

              {isLoading ? (
                <div className="py-16 text-center text-slate-400">
                  <Zap className="w-5 h-5 animate-pulse text-indigo-400 mx-auto mb-2" />
                  <span className="text-xs">Computing similarity scores...</span>
                </div>
              ) : data?.results?.length ? (
                <div className="space-y-3">
                  {data.results.map((r, i) => (
                    <div
                      key={r.chunk_id || i}
                      className="p-3.5 rounded-xl bg-[#0e101a] border border-white/[0.04] space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-mono font-bold text-indigo-400">Rank #{i + 1}</span>
                        <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400">
                          <span>score: {r.score.toFixed(3)}</span>
                          {r.rerank_score != null && (
                            <span className="text-emerald-400 font-bold">
                              rerank: {r.rerank_score.toFixed(3)}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="text-xs font-semibold text-slate-200 truncate">
                        {r.document_name}
                      </div>

                      <p className="text-[11px] text-slate-400 leading-relaxed font-mono line-clamp-3">
                        {r.content}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-16 text-center text-slate-500 text-xs">
                  Run a query above to see ranked candidate chunks.
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
