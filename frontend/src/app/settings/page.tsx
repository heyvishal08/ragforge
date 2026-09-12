"use client";

import { Settings, Cpu, Database, Shield, Sliders, CheckCircle2 } from "lucide-react";

const configSections = [
  {
    title: "Inference & LLM Provider",
    icon: Cpu,
    items: [
      { label: "Provider", value: "Groq Cloud LPU", desc: "Ultra-fast hardware-accelerated inference" },
      { label: "Model Architecture", value: "llama-3.3-70b-versatile", desc: "Configured via GROQ_MODEL" },
      { label: "Sampling Temperature", value: "0.3", desc: "Low temperature for strict factual grounding" },
    ],
  },
  {
    title: "Dense Embedding Layer",
    icon: Database,
    items: [
      { label: "Embedding Provider", value: "Sentence Transformers (Local)", desc: "PyTorch neural embedding pipeline" },
      { label: "Model Name", value: "all-MiniLM-L6-v2", desc: "384-dimensional dense representation" },
      { label: "Vector Indexing", value: "PostgreSQL pgvector / HNSW", desc: "Cosine similarity distance operator" },
    ],
  },
  {
    title: "Hybrid Retrieval & Reranking",
    icon: Sliders,
    items: [
      { label: "Search Strategy", value: "Hybrid (pgvector + tsvector)", desc: "Merged via Reciprocal Rank Fusion (k=60)" },
      { label: "Initial Recall (Top-K)", value: "20 chunks", desc: "Broad candidate collection before reranking" },
      { label: "Cross-Encoder Reranker", value: "cross-encoder/ms-marco-MiniLM-L-6-v2", desc: "Joint-attention neural reranking" },
      { label: "Final Context Budget", value: "8 chunks", desc: "Authoritative excerpts passed to LLM" },
    ],
  },
  {
    title: "Security & Guardrails",
    icon: Shield,
    items: [
      { label: "Evidence Quality Threshold", value: "0.30", desc: "Refuses generation if evidence score is too low" },
      { label: "Prompt Injection Isolation", value: "Enabled", desc: "Document text treated strictly as untrusted data" },
      { label: "Structured CSV Sandbox", value: "Read-only AST validator", desc: "Blocks unauthorized OS, exec, or SQL calls" },
    ],
  },
];

export default function SettingsPage() {
  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="pb-2 border-b border-white/[0.06]">
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          System Configuration
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Active runtime configurations across LLM inference, embedding, retrieval, and security layers.
        </p>
      </div>

      {/* Configuration Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {configSections.map((section) => (
          <div
            key={section.title}
            className="glass-panel p-6 rounded-2xl border border-white/[0.06] bg-[#141724]/70 space-y-4 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center gap-3 pb-3 border-b border-white/[0.06] mb-4">
                <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                  <section.icon className="w-4 h-4 text-indigo-400" />
                </div>
                <h3 className="text-base font-bold text-white tracking-tight">{section.title}</h3>
              </div>

              <div className="space-y-3">
                {section.items.map((item) => (
                  <div
                    key={item.label}
                    className="p-3 rounded-xl bg-[#0e101a] border border-white/[0.04] flex items-center justify-between gap-3"
                  >
                    <div>
                      <div className="text-xs font-bold text-slate-200">{item.label}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">{item.desc}</div>
                    </div>

                    <span className="text-xs font-mono font-bold text-indigo-300 bg-indigo-500/10 px-2.5 py-1 rounded-lg border border-indigo-500/20 shrink-0">
                      {item.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
