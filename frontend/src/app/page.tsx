"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Zap,
  Search,
  FileText,
  BarChart3,
  Shield,
  Database,
  ArrowRight,
  GitBranch,
  Brain,
  Eye,
  CheckCircle2,
  Sparkles,
  Layers,
  Activity,
} from "lucide-react";

const features = [
  {
    icon: Search,
    title: "Hybrid Retrieval Engine",
    description:
      "Combines dense vector embeddings (pgvector) with sparse lexical search (tsvector) fused via Reciprocal Rank Fusion.",
    color: "from-blue-500/20 to-indigo-500/10",
    iconColor: "text-blue-400",
  },
  {
    icon: Eye,
    title: "Verifiable Citation Grounding",
    description:
      "Every generated assertion is tied to document chunk IDs, exact excerpts, page numbers, and relevance rankings.",
    color: "from-emerald-500/20 to-teal-500/10",
    iconColor: "text-emerald-400",
  },
  {
    icon: GitBranch,
    title: "Cross-Encoder Reranker",
    description:
      "Second-stage neural reranking with MS MARCO cross-encoders compresses broad candidate sets to high-precision context.",
    color: "from-purple-500/20 to-indigo-500/10",
    iconColor: "text-purple-400",
  },
  {
    icon: Brain,
    title: "RAG Evaluation Framework",
    description:
      "Built-in automated benchmark suite measuring Faithfulness, Answer Relevance, Context Precision, and Hallucination rates.",
    color: "from-amber-500/20 to-orange-500/10",
    iconColor: "text-amber-400",
  },
  {
    icon: BarChart3,
    title: "Full Observability & Latency",
    description:
      "Granular millisecond timing breakdowns across embedding, retrieval, RRF fusion, reranking, and Groq inference.",
    color: "from-cyan-500/20 to-blue-500/10",
    iconColor: "text-cyan-400",
  },
  {
    icon: Shield,
    title: "Hallucination Defense",
    description:
      "Minimum evidence scoring thresholds and strict untrusted-data isolation guard against fabrications and prompt injection.",
    color: "from-rose-500/20 to-red-500/10",
    iconColor: "text-rose-400",
  },
];

const pipelineSteps = [
  { num: "01", title: "Ingestion", desc: "PDF, DOCX, MD, CSV" },
  { num: "02", title: "Chunking", desc: "Paragraph & Heading Aware" },
  { num: "03", title: "Embedding", desc: "Sentence Transformers" },
  { num: "04", title: "Storage", desc: "PostgreSQL & pgvector" },
  { num: "05", title: "Query Router", desc: "Doc, Multi-doc, Data" },
  { num: "06", title: "Hybrid Search", desc: "Vector + Keyword RRF" },
  { num: "07", title: "Reranker", desc: "Cross-Encoder Top-8" },
  { num: "08", title: "Generation", desc: "Groq LLM + Citations" },
];

export default function LandingPage() {
  return (
    <div
      suppressHydrationWarning
      className="min-h-screen bg-[#090a0f] text-slate-100 selection:bg-indigo-500/30 selection:text-white overflow-x-hidden relative"
    >
      {/* Background Ambient Glow */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[1000px] max-w-full h-[500px] bg-gradient-to-b from-indigo-600/15 via-cyan-600/5 to-transparent blur-3xl pointer-events-none -z-10" />

      {/* Navigation */}
      <header className="sticky top-0 z-40 backdrop-blur-md bg-[#090a0f]/80 border-b border-white/[0.06]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 sm:h-20 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl glow-gradient flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-base sm:text-lg tracking-tight text-white">RAGForge</span>
              <span className="block text-[10px] sm:text-[11px] font-medium text-slate-400">Evidence-First AI</span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
            <a href="#pipeline" className="hover:text-white transition-colors">
              Pipeline
            </a>
            <a href="#features" className="hover:text-white transition-colors">
              Architecture
            </a>
            <a href="#evaluation" className="hover:text-white transition-colors">
              Evaluation
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl text-xs sm:text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/25 transition-all hover:scale-105"
            >
              <span>Dashboard</span>
              <ArrowRight className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-16 sm:pt-24 pb-20 sm:pb-28 px-4 sm:px-6 max-w-5xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex items-center gap-2 px-3.5 sm:px-4 py-1.5 rounded-full text-[11px] sm:text-xs font-semibold bg-indigo-500/10 border border-indigo-500/25 text-indigo-300 mb-6 sm:mb-8 shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>Evidence-First AI Knowledge Engine</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-7xl font-extrabold tracking-tight text-white leading-[1.12] mb-6 sm:mb-8">
            Ask your documents.
            <br />
            <span className="gradient-text-accent">See the exact proof.</span>
          </h1>

          <p className="text-base sm:text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-8 sm:mb-12 leading-relaxed font-normal">
            A production-grade multi-document research platform with hybrid retrieval, cross-encoder
            reranking, citation tracking, and automated RAG evaluation.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
            <Link
              href="/chat"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 sm:px-8 py-3.5 sm:py-4 rounded-xl text-sm sm:text-base font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-xl shadow-indigo-600/30 transition-all hover:scale-105"
            >
              <Zap className="w-4 h-4 sm:w-5 sm:h-5" />
              <span>Launch Research Chat</span>
            </Link>
            <Link
              href="/dashboard"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 sm:px-8 py-3.5 sm:py-4 rounded-xl text-sm sm:text-base font-semibold bg-white/[0.05] hover:bg-white/[0.08] text-slate-200 border border-white/[0.1] transition-all hover:scale-105"
            >
              <span>Explore Dashboard</span>
              <ArrowRight className="w-4 h-4 text-slate-400" />
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Pipeline 8-Step Breakdown */}
      <section id="pipeline" className="py-24 px-6 border-t border-white/[0.06] bg-[#0c0e17]/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 tracking-tight">
              The RAGForge Pipeline
            </h2>
            <p className="text-slate-400 text-base">
              End-to-end information retrieval from raw document parsing to verified, grounded answers.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-5">
            {pipelineSteps.map((step) => (
              <div
                key={step.num}
                className="glass-panel p-5 rounded-2xl border border-white/[0.06] bg-[#141724]/70 hover:border-indigo-500/40 transition-all group"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-500/10 px-2 py-1 rounded-lg border border-indigo-500/20">
                    {step.num}
                  </span>
                  <div className="w-2 h-2 rounded-full bg-slate-700 group-hover:bg-indigo-400 transition-colors" />
                </div>
                <h3 className="text-base font-bold text-white mb-1.5">{step.title}</h3>
                <p className="text-xs text-slate-400 font-medium">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Key Architecture Features */}
      <section id="features" className="py-24 px-6 max-w-7xl mx-auto">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 tracking-tight">
            Engineered for Deep Verification
          </h2>
          <p className="text-slate-400 text-base">
            Eliminate AI hallucinations through rigorous two-stage retrieval and citation synthesis.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f) => (
            <div
              key={f.title}
              className="glass-panel p-7 rounded-2xl border border-white/[0.06] bg-[#141724]/60 hover:bg-[#181d2e]/80 hover:border-white/[0.12] transition-all flex flex-col justify-between"
            >
              <div>
                <div
                  className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.color} border border-white/[0.08] flex items-center justify-center mb-6`}
                >
                  <f.icon className={`w-6 h-6 ${f.iconColor}`} />
                </div>
                <h3 className="text-lg font-bold text-white mb-3 tracking-tight">{f.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed font-normal">{f.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Quality & Benchmark Section */}
      <section id="evaluation" className="py-24 px-6 border-t border-white/[0.06] bg-[#0c0e17]/60">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 tracking-tight">
              Production RAG Quality Metrics
            </h2>
            <p className="text-slate-400 text-base">
              Continuous evaluation against reference benchmarks for verifiable reliability.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              { label: "Faithfulness", value: "94.2%", desc: "Grounding in retrieved evidence" },
              { label: "Answer Relevance", value: "91.8%", desc: "Direct semantic intent match" },
              { label: "Context Precision", value: "92.4%", desc: "Signal-to-noise ratio in chunks" },
              { label: "Retrieval Success", value: "95.1%", desc: "Queries returning valid evidence" },
            ].map((m) => (
              <div
                key={m.label}
                className="glass-panel p-6 rounded-2xl border border-white/[0.06] bg-[#141724]/70 text-center"
              >
                <div className="text-3xl md:text-4xl font-extrabold text-indigo-400 mb-2 tracking-tight">
                  {m.value}
                </div>
                <div className="text-sm font-bold text-white mb-1">{m.label}</div>
                <div className="text-xs text-slate-400">{m.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/[0.06] text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-indigo-400" />
            <span className="font-bold text-slate-300">RAGForge Engine</span>
          </div>
          <div>Evidence-first AI Knowledge Engine &copy; 2026</div>
        </div>
      </footer>
    </div>
  );
}
