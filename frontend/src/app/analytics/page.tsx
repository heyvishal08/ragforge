"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  BarChart3,
  Clock,
  CheckCircle2,
  AlertCircle,
  Database,
  FileText,
  Zap,
  Activity,
  X,
} from "lucide-react";
import api from "@/lib/api";
import type { AnalyticsSummary, QueryLog } from "@/types";
import { formatLatency, formatDate } from "@/lib/utils";

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [queryLogs, setQueryLogs] = useState<QueryLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedQuery, setSelectedQuery] = useState<QueryLog | null>(null);

  useEffect(() => {
    Promise.all([
      api.get<AnalyticsSummary>("/analytics/summary"),
      api.get<QueryLog[]>("/analytics/queries"),
    ])
      .then(([summary, logs]) => {
        setAnalytics(summary);
        setQueryLogs(logs);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const latencyData = queryLogs
    .slice(0, 15)
    .reverse()
    .map((q, i) => ({
      name: `Q#${i + 1}`,
      Retrieval: Math.round(q.vector_search_latency_ms || 35),
      Reranking: Math.round(q.rerank_latency_ms || 45),
      Generation: Math.round(q.generation_latency_ms || 220),
    }));

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="pb-2 border-b border-white/[0.06]">
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          Observability & Analytics
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Millisecond query latency breakdowns, token volume tracking, and execution telemetry.
        </p>
      </div>

      {/* 4 KPI Summary Cards */}
      {analytics && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
          {[
            {
              label: "Total Queries Run",
              value: analytics.total_queries,
              icon: BarChart3,
              color: "text-indigo-400",
              bg: "bg-indigo-500/10 border-indigo-500/20",
            },
            {
              label: "Average Latency",
              value: formatLatency(analytics.avg_latency_ms),
              icon: Clock,
              color: "text-amber-400",
              bg: "bg-amber-500/10 border-amber-500/20",
            },
            {
              label: "Success Rate",
              value: `${analytics.success_rate.toFixed(1)}%`,
              icon: CheckCircle2,
              color: "text-emerald-400",
              bg: "bg-emerald-500/10 border-emerald-500/20",
            },
            {
              label: "Indexed Chunks",
              value: analytics.total_chunks,
              icon: Database,
              color: "text-cyan-400",
              bg: "bg-cyan-500/10 border-cyan-500/20",
            },
          ].map((item) => (
            <div
              key={item.label}
              className="glass-panel p-5 rounded-2xl border border-white/[0.06] bg-[#141724]/70 flex items-center gap-4"
            >
              <div
                className={`w-12 h-12 rounded-xl border flex items-center justify-center shrink-0 ${item.bg}`}
              >
                <item.icon className={`w-6 h-6 ${item.color}`} />
              </div>
              <div className="min-w-0">
                <div className="text-2xl font-extrabold text-white tracking-tight truncate">
                  {item.value}
                </div>
                <div className="text-xs font-semibold text-slate-400 truncate">{item.label}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Stacked Latency Chart Card */}
      <div className="glass-panel p-4 sm:p-6 rounded-2xl border border-white/[0.06] bg-[#141724]/70 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Pipeline Stage Latency Breakdown (ms)
            </h3>
            <p className="text-xs text-slate-400">
              Granular latency distribution across Retrieval, Reranking, and LLM Generation.
            </p>
          </div>
          <Activity className="w-5 h-5 text-indigo-400" />
        </div>

        <div className="h-[280px] w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={latencyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} unit="ms" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0e101a",
                  borderColor: "rgba(255,255,255,0.1)",
                  borderRadius: "12px",
                  fontSize: "12px",
                  boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5)",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
              <Bar dataKey="Retrieval" stackId="a" fill="#06b6d4" radius={[0, 0, 0, 0]} />
              <Bar dataKey="Reranking" stackId="a" fill="#f59e0b" radius={[0, 0, 0, 0]} />
              <Bar dataKey="Generation" stackId="a" fill="#6366f1" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Query Logs Table and Detail View */}
      <div className="flex flex-col lg:flex-row gap-6 lg:gap-8 items-start">
        <div className={selectedQuery ? "w-full lg:w-1/2" : "w-full"}>
          <div className="glass-panel p-4 sm:p-6 rounded-2xl border border-white/[0.06] bg-[#141724]/70">
            <h3 className="text-base font-bold text-white tracking-tight mb-4 pb-3 border-b border-white/[0.06]">
              Query Execution Logs
            </h3>

            {queryLogs.length === 0 ? (
              <div className="py-12 text-center text-slate-500 text-xs">
                No queries logged yet. Run queries from Research Chat to populate logs.
              </div>
            ) : (
              <div className="space-y-2.5">
                {queryLogs.map((q) => (
                  <div
                    key={q.id}
                    onClick={() => setSelectedQuery(q)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all flex items-center justify-between gap-4 ${
                      selectedQuery?.id === q.id
                        ? "border-indigo-500/50 bg-[#181d2e]"
                        : "border-white/[0.04] bg-white/[0.02] hover:bg-white/[0.04]"
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      <div className="min-w-0">
                        <div className="text-xs font-bold text-slate-200 truncate">{q.query}</div>
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          {q.retrieval_strategy} • {formatDate(q.created_at)}
                        </div>
                      </div>
                    </div>

                    <span className="text-xs font-mono font-bold text-indigo-400 shrink-0">
                      {formatLatency(q.total_latency_ms || 0)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Selected Query Inspector */}
        {selectedQuery && (
          <div className="w-full lg:w-1/2 glass-panel p-4 sm:p-6 rounded-2xl border border-white/[0.06] bg-[#141724]/90 lg:sticky lg:top-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
              <h3 className="text-base font-bold text-white tracking-tight">Query Detail</h3>
              <button
                onClick={() => setSelectedQuery(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-3.5 rounded-xl bg-[#0e101a] border border-white/[0.06] text-xs text-slate-300 font-mono">
              &ldquo;{selectedQuery.query}&rdquo;
            </div>

            <div className="space-y-2 text-xs">
              {[
                { label: "Query Intent", val: selectedQuery.query_type },
                { label: "Retrieval Strategy", val: selectedQuery.retrieval_strategy },
                { label: "Inference Model", val: selectedQuery.model },
                { label: "Candidates Retrieved", val: selectedQuery.retrieved_count },
                { label: "Context After Rerank", val: selectedQuery.final_count },
              ].map((item) => (
                <div
                  key={item.label}
                  className="flex justify-between p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04]"
                >
                  <span className="text-slate-400">{item.label}</span>
                  <span className="font-bold text-white capitalize">{item.val ?? "—"}</span>
                </div>
              ))}
            </div>

            <div className="pt-2 border-t border-white/[0.06]">
              <div className="text-[11px] font-bold uppercase text-slate-400 mb-2">
                Stage Latencies
              </div>
              <div className="space-y-1.5 text-xs font-mono">
                {[
                  { label: "Vector Search", ms: selectedQuery.vector_search_latency_ms },
                  { label: "Reranking", ms: selectedQuery.rerank_latency_ms },
                  { label: "Generation", ms: selectedQuery.generation_latency_ms },
                  { label: "Total", ms: selectedQuery.total_latency_ms, bold: true },
                ].map((t) => (
                  <div key={t.label} className="flex justify-between">
                    <span className={t.bold ? "font-bold text-white" : "text-slate-400"}>
                      {t.label}
                    </span>
                    <span className={t.bold ? "text-indigo-400 font-bold" : "text-slate-300"}>
                      {t.ms != null ? formatLatency(t.ms) : "—"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
