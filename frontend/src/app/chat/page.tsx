"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Loader2,
  Database,
  FileText,
  Eye,
  Clock,
  Zap,
  ChevronRight,
  Copy,
  Check,
  X,
  BarChart3,
  Shield,
  Search,
  Sparkles,
  Info,
  RotateCcw,
} from "lucide-react";
import api from "@/lib/api";
import type { KnowledgeBase, Citation, RetrievalMetadata, Confidence, Document as DocType } from "@/types";
import { formatLatency } from "@/lib/utils";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  retrieval_metadata?: RetrievalMetadata | null;
  confidence?: Confidence | null;
}

function ChatContent() {
  const searchParams = useSearchParams();
  const initialKb = searchParams.get("kb") || "";

  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKb, setSelectedKb] = useState(initialKb);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [showRetrieval, setShowRetrieval] = useState(false);
  const [activeMetadata, setActiveMetadata] = useState<RetrievalMetadata | null>(null);
  const [activeConfidence, setActiveConfidence] = useState<Confidence | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 1. Fetch available knowledge bases
  useEffect(() => {
    api
      .get<KnowledgeBase[]>("/knowledge-bases")
      .then((data) => {
        setKnowledgeBases(data);
        if (!selectedKb && data.length > 0) {
          setSelectedKb(data[0].id);
        }
      })
      .catch(() => {});
  }, [selectedKb]);

  // 2. Restore chat history from sessionStorage when selectedKb changes
  useEffect(() => {
    if (!selectedKb || typeof window === "undefined") return;
    try {
      const saved = sessionStorage.getItem(`ragforge_chat_${selectedKb}`);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.messages && Array.isArray(parsed.messages)) {
          setMessages(parsed.messages);
        } else {
          setMessages([]);
        }
        if (parsed.conversationId) {
          setConversationId(parsed.conversationId);
        } else {
          setConversationId(null);
        }
      } else {
        setMessages([]);
        setConversationId(null);
      }
    } catch {
      setMessages([]);
      setConversationId(null);
    }
  }, [selectedKb]);

  // 3. Persist messages & conversationId to sessionStorage
  useEffect(() => {
    if (!selectedKb || typeof window === "undefined") return;
    try {
      const key = `ragforge_chat_${selectedKb}`;
      if (messages.length > 0) {
        sessionStorage.setItem(
          key,
          JSON.stringify({ messages, conversationId })
        );
      } else {
        sessionStorage.removeItem(key);
      }
    } catch {}
  }, [messages, conversationId, selectedKb]);

  // 4. Fetch document-specific suggested questions for the active Knowledge Base
  useEffect(() => {
    if (!selectedKb) {
      setSuggestedQuestions([]);
      return;
    }
    api
      .get<DocType[]>("/documents", { knowledge_base_id: selectedKb })
      .then((docs) => {
        const questions: string[] = [];
        docs.forEach((doc) => {
          if (doc.suggested_questions && Array.isArray(doc.suggested_questions)) {
            doc.suggested_questions.forEach((q) => {
              if (typeof q === "string" && !questions.includes(q)) {
                questions.push(q);
              }
            });
          }
        });
        if (questions.length === 0 && docs.length > 0) {
          docs.forEach((d) => {
            questions.push(`Summarize ${d.filename}`);
          });
          questions.push("What are the key requirements and deliverables?");
          questions.push("What are the costs, pricing, and timelines mentioned?");
        }
        setSuggestedQuestions(questions.slice(0, 4));
      })
      .catch(() => {});
  }, [selectedKb]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSend = async () => {
    if (!input.trim() || !selectedKb || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${api.base}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          knowledge_base_id: selectedKb,
          conversation_id: conversationId,
          query: userMessage.content,
          retrieval_strategy: "hybrid",
        }),
      });

      if (!response.ok) throw new Error("Chat request failed");

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = "";
      let assistantCitations: Citation[] = [];
      let retrievalMeta: RetrievalMetadata | null = null;
      let confidence: Confidence | null = null;

      const assistantId = (Date.now() + 1).toString();
      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: "assistant",
          content: "",
        },
      ]);

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value);
          const lines = text.split("\n\n");

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === "content") {
                assistantContent = data.content;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId ? { ...m, content: assistantContent } : m
                  )
                );
              } else if (data.type === "citations") {
                assistantCitations = data.citations;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId ? { ...m, citations: assistantCitations } : m
                  )
                );
              } else if (data.type === "metadata") {
                retrievalMeta = data.retrieval_metadata;
                confidence = data.confidence;
                if (data.conversation_id) setConversationId(data.conversation_id);
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, retrieval_metadata: retrievalMeta, confidence }
                      : m
                  )
                );
              }
            } catch {}
          }
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 2).toString(),
          role: "assistant",
          content:
            "I couldn't complete retrieval for this request. Please ensure the backend is running and documents are indexed.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderContent = (content: string, citations?: Citation[]) => {
    const parts = content.split(/(\[\d+\])/g);
    return parts.map((part, i) => {
      const match = part.match(/^\[(\d+)\]$/);
      if (match) {
        const idx = parseInt(match[1]);
        const cit = citations?.find((c) => c.citation_index === idx);
        return (
          <button
            key={i}
            onClick={() => {
              if (cit) {
                setSelectedCitation(cit);
                setShowRetrieval(false);
              }
            }}
            className="inline-flex items-center justify-center min-w-[22px] h-[20px] px-1.5 rounded-md text-[11px] font-bold mx-0.5 bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500 hover:text-white transition-all transform hover:scale-105 align-baseline"
          >
            {idx}
          </button>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  const activeKbName =
    knowledgeBases.find((k) => k.id === selectedKb)?.name || "Select Knowledge Base";

  return (
    <div className="h-[calc(100vh-5rem)] flex gap-6">
      {/* Left Column: Knowledge Base Selector */}
      <div className="w-64 shrink-0 glass-panel p-4 flex flex-col border border-white/[0.06] bg-[#141724]/70">
        <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 px-2 flex items-center justify-between">
          <span>Knowledge Bases</span>
          <Database className="w-3.5 h-3.5 text-indigo-400" />
        </div>

        <div className="flex-1 space-y-1.5 overflow-y-auto pr-1">
          {knowledgeBases.map((kb) => (
            <button
              key={kb.id}
              onClick={() => {
                setSelectedKb(kb.id);
                setSelectedCitation(null);
                setShowRetrieval(false);
              }}
              className={`w-full text-left p-3 rounded-xl transition-all flex items-start gap-3 text-xs ${
                selectedKb === kb.id
                  ? "bg-indigo-600/15 border border-indigo-500/30 text-white font-semibold shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.03] border border-transparent"
              }`}
            >
              <Database
                className={`w-4 h-4 shrink-0 mt-0.5 ${
                  selectedKb === kb.id ? "text-indigo-400" : "text-slate-400"
                }`}
              />
              <div className="min-w-0">
                <div className="truncate font-semibold text-slate-200">{kb.name}</div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  {kb.document_count} doc{kb.document_count !== 1 ? "s" : ""}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Center Column: Conversation View */}
      <div className="flex-1 flex flex-col glass-panel rounded-2xl border border-white/[0.06] bg-[#141724]/60 min-w-0 overflow-hidden">
        {/* Chat Header Bar */}
        <div className="h-16 px-6 border-b border-white/[0.06] flex items-center justify-between bg-[#141724]/80 backdrop-blur-md shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <div>
              <div className="text-sm font-bold text-white tracking-tight">{activeKbName}</div>
              <div className="text-[11px] text-slate-400">Grounded Generation Active</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {messages.length > 0 && (
              <button
                onClick={() => {
                  setMessages([]);
                  setConversationId(null);
                  setSelectedCitation(null);
                  setShowRetrieval(false);
                  if (selectedKb && typeof window !== "undefined") {
                    sessionStorage.removeItem(`ragforge_chat_${selectedKb}`);
                  }
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 hover:text-white border border-white/[0.08] transition-colors"
                title="Start a fresh conversation"
              >
                <RotateCcw className="w-3.5 h-3.5 text-indigo-400" />
                <span>New Chat</span>
              </button>
            )}
            <div className="text-xs font-semibold px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              Groq LPU (llama-3.3-70b-versatile)
            </div>
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center p-8">
              <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-4 text-indigo-400 shadow-lg shadow-indigo-500/10">
                <Zap className="w-7 h-7" />
              </div>
              <h2 className="text-xl font-bold text-white mb-2 tracking-tight">
                Research Chat Ready
              </h2>
              <p className="text-sm text-slate-400 max-w-md leading-relaxed">
                Ask any question across your indexed documents. Answers are strictly grounded in
                evidence and cited with exact references.
              </p>

              <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-w-lg w-full">
                {(suggestedQuestions.length > 0
                  ? suggestedQuestions
                  : [
                      "Summarize the uploaded documents",
                      "What are the main requirements and specifications?",
                      "What are the costs and pricing details mentioned?",
                      "Compare key features and timelines across the files",
                    ]
                ).map((suggested) => (
                  <button
                    key={suggested}
                    onClick={() => {
                      setInput(suggested);
                    }}
                    className="p-3 text-left rounded-xl bg-white/[0.02] border border-white/[0.06] hover:border-indigo-500/30 hover:bg-white/[0.04] text-xs text-slate-300 transition-colors line-clamp-2"
                    title={suggested}
                  >
                    &ldquo;{suggested}&rdquo;
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl p-5 ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
                    : "bg-[#1c2136] text-slate-200 border border-white/[0.08] shadow-md"
                }`}
              >
                <div className="text-sm leading-relaxed whitespace-pre-wrap font-normal">
                  {msg.role === "assistant"
                    ? renderContent(msg.content, msg.citations)
                    : msg.content}
                </div>

                {/* Citations Footer */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-4 pt-3.5 border-t border-white/[0.08] flex flex-wrap items-center gap-2">
                    <span className="text-[11px] font-semibold text-slate-400">Sources:</span>
                    {msg.citations.map((cit) => (
                      <button
                        key={cit.citation_index}
                        onClick={() => {
                          setSelectedCitation(cit);
                          setShowRetrieval(false);
                        }}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-white/[0.06] hover:bg-indigo-500/20 hover:border-indigo-500/40 border border-white/[0.08] text-slate-200 transition-all"
                      >
                        <FileText className="w-3.5 h-3.5 text-indigo-400" />
                        <span>[{cit.citation_index}]</span>
                        <span className="max-w-[120px] truncate">{cit.document_name}</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Metadata & Actions */}
                {msg.role === "assistant" && (
                  <div className="mt-3.5 pt-2.5 border-t border-white/[0.06] flex items-center justify-between text-xs text-slate-400">
                    <div className="flex items-center gap-3">
                      {msg.retrieval_metadata && (
                        <button
                          onClick={() => {
                            setActiveMetadata(msg.retrieval_metadata!);
                            setActiveConfidence(msg.confidence || null);
                            setShowRetrieval(true);
                            setSelectedCitation(null);
                          }}
                          className="flex items-center gap-1.5 text-indigo-400 hover:text-indigo-300 font-semibold transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Explain Retrieval
                          {msg.retrieval_metadata.timings && (
                            <span className="text-[11px] font-mono text-slate-400 ml-1">
                              ({formatLatency(msg.retrieval_metadata.timings.total_ms)})
                            </span>
                          )}
                        </button>
                      )}
                    </div>

                    <button
                      onClick={() => handleCopy(msg.id, msg.content)}
                      className="text-slate-400 hover:text-slate-200 transition-colors p-1"
                    >
                      {copiedId === msg.id ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="p-4 rounded-2xl bg-[#1c2136] border border-white/[0.08] flex items-center gap-3 text-slate-300 text-xs font-medium">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                <span>Searching knowledge base & synthesizing grounded answer...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-white/[0.06] bg-[#141724]/90">
          <div className="flex items-center gap-3 p-2.5 rounded-2xl bg-[#1a1e30] border border-white/[0.08] focus-within:border-indigo-500/50 transition-colors shadow-inner">
            <input
              type="text"
              placeholder={
                selectedKb
                  ? "Ask a question about your indexed documents..."
                  : "Select a knowledge base to start querying"
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              disabled={!selectedKb || loading}
              className="flex-1 bg-transparent px-3 py-1.5 text-sm text-slate-100 placeholder:text-slate-400 outline-none"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || !selectedKb || loading}
              className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 disabled:pointer-events-none text-white shadow-md shadow-indigo-600/20 transition-all flex items-center gap-2 shrink-0"
            >
              <span>Send</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Right Column: Evidence / Explain Retrieval Drawer */}
      <AnimatePresence>
        {(selectedCitation || showRetrieval) && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 400, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="shrink-0 glass-panel border border-white/[0.06] bg-[#141724]/85 flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="h-16 px-6 border-b border-white/[0.06] flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2">
                {selectedCitation ? (
                  <>
                    <FileText className="w-4 h-4 text-indigo-400" />
                    <span className="text-sm font-bold text-white">Evidence Inspector</span>
                  </>
                ) : (
                  <>
                    <Eye className="w-4 h-4 text-cyan-400" />
                    <span className="text-sm font-bold text-white">Explain Retrieval</span>
                  </>
                )}
              </div>

              <button
                onClick={() => {
                  setSelectedCitation(null);
                  setShowRetrieval(false);
                }}
                className="p-1 rounded-lg text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Evidence Inspector View */}
              {selectedCitation && !showRetrieval && (
                <div className="space-y-5">
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                      Document Source
                    </div>
                    <div className="text-sm font-bold text-slate-100 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                      <span className="truncate">{selectedCitation.document_name}</span>
                    </div>
                  </div>

                  {selectedCitation.page_number && (
                    <div>
                      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                        Location
                      </div>
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-white/[0.05] border border-white/[0.08] text-slate-200">
                        Page {selectedCitation.page_number}
                      </span>
                    </div>
                  )}

                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                      Retrieved Excerpt
                    </div>
                    <div className="p-4 rounded-xl bg-[#0e101a] border border-white/[0.06] text-xs text-slate-300 leading-relaxed font-mono">
                      &ldquo;{selectedCitation.chunk_content}&rdquo;
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-2">
                    <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                      <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">
                        Retrieval
                      </div>
                      <div className="text-xs font-bold text-cyan-400 capitalize">
                        {selectedCitation.retrieval_method || "Hybrid"}
                      </div>
                    </div>

                    {selectedCitation.rerank_score != null && (
                      <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                        <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">
                          Rerank Score
                        </div>
                        <div className="text-xs font-bold text-emerald-400">
                          {selectedCitation.rerank_score.toFixed(3)}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Explain Retrieval Observability View */}
              {showRetrieval && activeMetadata && (
                <div className="space-y-6">
                  {/* Pipeline Stage Indicators */}
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">
                      Processing Pipeline
                    </div>
                    <div className="space-y-2">
                      {[
                        { label: "Query Routing", val: activeMetadata.query_type },
                        { label: "Retrieval Strategy", val: activeMetadata.retrieval_strategy },
                        { label: "Candidates Retrieved", val: `${activeMetadata.retrieved_candidates} chunks` },
                        { label: "Cross-Encoder Context", val: `${activeMetadata.final_evidence_count} chunks` },
                      ].map((item) => (
                        <div
                          key={item.label}
                          className="flex items-center justify-between p-3 rounded-xl bg-[#0e101a] border border-white/[0.04] text-xs"
                        >
                          <span className="text-slate-400 font-medium">{item.label}</span>
                          <span className="font-bold text-slate-200 capitalize">{item.val}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Latency Breakdown */}
                  {activeMetadata.timings && (
                    <div>
                      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">
                        Latency Breakdown
                      </div>
                      <div className="space-y-2.5 p-4 rounded-xl bg-[#0e101a] border border-white/[0.04]">
                        {[
                          { label: "Retrieval", ms: activeMetadata.timings.retrieval_ms },
                          { label: "Reranking", ms: activeMetadata.timings.rerank_ms },
                          { label: "Generation", ms: activeMetadata.timings.generation_ms },
                          { label: "Total Latency", ms: activeMetadata.timings.total_ms, bold: true },
                        ].map((t) => (
                          <div key={t.label} className="flex items-center justify-between text-xs">
                            <span className={t.bold ? "font-bold text-white" : "text-slate-400"}>
                              {t.label}
                            </span>
                            <span
                              className={`font-mono font-bold ${
                                t.bold ? "text-indigo-400" : "text-slate-300"
                              }`}
                            >
                              {formatLatency(t.ms)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Confidence Indicators */}
                  {activeConfidence && (
                    <div>
                      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">
                        Derived Confidence
                      </div>
                      <div className="space-y-3.5 p-4 rounded-xl bg-[#0e101a] border border-white/[0.04]">
                        {[
                          { label: "Evidence Confidence", val: activeConfidence.evidence_confidence },
                          { label: "Context Quality", val: activeConfidence.evidence_quality },
                          { label: "Source Coverage", val: activeConfidence.retrieval_coverage },
                        ].map((c) => (
                          <div key={c.label}>
                            <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1.5">
                              <span>{c.label}</span>
                              <span className="text-indigo-400">{c.val}%</span>
                            </div>
                            <div className="h-1.5 rounded-full bg-white/[0.08] overflow-hidden">
                              <div
                                className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-full"
                                style={{ width: `${c.val}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[50vh]">
          <div className="flex items-center gap-3 text-slate-400">
            <Zap className="w-5 h-5 animate-pulse text-indigo-400" />
            <span className="text-sm font-medium">Loading research chat...</span>
          </div>
        </div>
      }
    >
      <ChatContent />
    </Suspense>
  );
}
