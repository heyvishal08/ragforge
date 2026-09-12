"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Database,
  FileText,
  MessageSquare,
  Clock,
  CheckCircle2,
  TrendingUp,
  Zap,
  ArrowRight,
  AlertCircle,
  Plus,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import type { AnalyticsSummary, KnowledgeBase } from "@/types";
import { formatLatency } from "@/lib/utils";

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [analyticsData, kbData] = await Promise.all([
          api.get<AnalyticsSummary>("/analytics/summary"),
          api.get<KnowledgeBase[]>("/knowledge-bases"),
        ]);
        setAnalytics(analyticsData);
        setKnowledgeBases(kbData);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="flex items-center gap-3 text-slate-400">
          <Zap className="w-5 h-5 animate-pulse text-indigo-400" />
          <span className="text-sm font-medium">Loading workspace metrics...</span>
        </div>
      </div>
    );
  }

  const stats = [
    {
      label: "Knowledge Bases",
      value: analytics?.total_knowledge_bases ?? 0,
      icon: Database,
      color: "text-indigo-400",
      bg: "bg-indigo-500/10 border-indigo-500/20",
      href: "/knowledge-bases",
    },
    {
      label: "Indexed Documents",
      value: analytics?.total_documents ?? 0,
      icon: FileText,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10 border-cyan-500/20",
      href: "/documents",
    },
    {
      label: "Total Queries Run",
      value: analytics?.total_queries ?? 0,
      icon: MessageSquare,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10 border-emerald-500/20",
      href: "/analytics",
    },
    {
      label: "Average Latency",
      value: formatLatency(analytics?.avg_latency_ms ?? 0),
      icon: Clock,
      color: "text-amber-400",
      bg: "bg-amber-500/10 border-amber-500/20",
      href: "/analytics",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-white/[0.06]">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
            Dashboard Overview
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time status of your knowledge bases, document indexing, and retrieval performance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/chat"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 transition-all hover:scale-105"
          >
            <MessageSquare className="w-4 h-4" />
            Start Research Chat
          </Link>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center gap-3 text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error} — Verify that your backend is active at http://localhost:8000</span>
        </div>
      )}

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {stats.map((stat) => (
          <Link
            key={stat.label}
            href={stat.href}
            className="glass-panel p-6 rounded-2xl border border-white/[0.06] bg-[#141724]/70 hover:bg-[#181d2e] hover:border-white/[0.12] transition-all group block"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`w-10 h-10 rounded-xl border flex items-center justify-center ${stat.bg}`}>
                <stat.icon className={`w-5 h-5 ${stat.color}`} />
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-white group-hover:translate-x-0.5 transition-all" />
            </div>
            <div className="text-3xl font-extrabold text-white tracking-tight mb-1">{stat.value}</div>
            <div className="text-xs font-semibold text-slate-400">{stat.label}</div>
          </Link>
        ))}
      </div>

      {/* 2-Column Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Knowledge Bases Section */}
        <div className="glass-panel p-6 rounded-2xl border border-white/[0.06] bg-[#141724]/70">
          <div className="flex items-center justify-between mb-6 pb-3 border-b border-white/[0.06]">
            <div className="flex items-center gap-2.5">
              <Database className="w-5 h-5 text-indigo-400" />
              <h2 className="text-base font-bold text-white tracking-tight">Active Knowledge Bases</h2>
            </div>
            <Link
              href="/knowledge-bases"
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors"
            >
              View all <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {knowledgeBases.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <Database className="w-10 h-10 mx-auto mb-3 text-slate-400" />
              <p className="text-sm font-medium mb-4">No knowledge bases found</p>
              <Link
                href="/knowledge-bases"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                Create Knowledge Base
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {knowledgeBases.slice(0, 4).map((kb) => (
                <div
                  key={kb.id}
                  className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] hover:border-white/[0.08] transition-colors flex items-center justify-between"
                >
                  <div className="min-w-0 pr-3">
                    <div className="text-sm font-bold text-white truncate">{kb.name}</div>
                    <div className="text-xs text-slate-400 mt-0.5 flex items-center gap-2">
                      <span>{kb.document_count} indexed docs</span>
                      <span>•</span>
                      <span>{new Date(kb.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  <Link
                    href={`/chat?kb=${kb.id}`}
                    className="shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 hover:bg-indigo-500/20 transition-colors flex items-center gap-1.5"
                  >
                    Chat <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Activity / Query Logs Section */}
        <div className="glass-panel p-6 rounded-2xl border border-white/[0.06] bg-[#141724]/70">
          <div className="flex items-center justify-between mb-6 pb-3 border-b border-white/[0.06]">
            <div className="flex items-center gap-2.5">
              <MessageSquare className="w-5 h-5 text-cyan-400" />
              <h2 className="text-base font-bold text-white tracking-tight">Recent Queries</h2>
            </div>
            <Link
              href="/analytics"
              className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
            >
              Observability <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {!analytics?.recent_queries?.length ? (
            <div className="text-center py-12 text-slate-400">
              <MessageSquare className="w-10 h-10 mx-auto mb-3 text-slate-400" />
              <p className="text-sm font-medium mb-1">No queries logged yet</p>
              <p className="text-xs text-slate-400 mb-4">Start a research chat to populate query analytics.</p>
              <Link
                href="/chat"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500 transition-colors"
              >
                Open Chat
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {analytics.recent_queries.slice(0, 4).map((q) => (
                <div
                  key={q.id}
                  className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] flex items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-slate-200 truncate">{q.query}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {q.retrieval_strategy} • {q.model || "Groq"}
                      </div>
                    </div>
                  </div>

                  <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-lg border border-indigo-500/20 shrink-0">
                    {formatLatency(q.total_latency_ms ?? 0)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
