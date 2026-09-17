"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  Upload,
  Trash2,
  Eye,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertCircle,
  Loader2,
  File,
  FileSpreadsheet,
  Layers,
  X,
  Plus,
} from "lucide-react";
import api from "@/lib/api";
import type { Document as DocType, KnowledgeBase, DocumentChunk } from "@/types";
import { formatBytes, formatDate } from "@/lib/utils";

const fileIcons: Record<string, React.ElementType> = {
  pdf: FileText,
  docx: File,
  txt: File,
  md: File,
  csv: FileSpreadsheet,
};

const statusStyles: Record<string, { color: string; bg: string; border: string }> = {
  READY: { color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  FAILED: { color: "text-rose-400", bg: "bg-rose-500/10", border: "border-rose-500/20" },
  UPLOADING: { color: "text-cyan-400", bg: "bg-cyan-500/10", border: "border-cyan-500/20" },
  PARSING: { color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" },
  CHUNKING: { color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" },
  EMBEDDING: { color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" },
  INDEXING: { color: "text-indigo-400", bg: "bg-indigo-500/10", border: "border-indigo-500/20" },
};

function DocumentsContent() {
  const searchParams = useSearchParams();
  const kbId = searchParams.get("kb");
  const [documents, setDocuments] = useState<DocType[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKb, setSelectedKb] = useState<string>(kbId || "");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<DocType | null>(null);
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [searchQuery, setSearchQuery] = useState("");

  const fetchDocs = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      if (selectedKb) params.knowledge_base_id = selectedKb;
      const data = await api.get<DocType[]>("/documents", params);
      setDocuments(data);
    } catch (err) {
      console.error("Failed to fetch documents", err);
    } finally {
      setLoading(false);
    }
  }, [selectedKb]);

  useEffect(() => {
    api
      .get<KnowledgeBase[]>("/knowledge-bases")
      .then((data) => {
        setKnowledgeBases(data);
        if (!selectedKb && data.length > 0) {
          setSelectedKb(data[0].id);
        }
      })
      .catch((err) => {
        console.error("Failed to load knowledge bases", err);
        setLoading(false);
      });
  }, [selectedKb]);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  useEffect(() => {
    const processing = documents.some((d) =>
      ["UPLOADING", "PARSING", "CHUNKING", "EMBEDDING", "INDEXING"].includes(d.status)
    );
    if (!processing) return;
    const interval = setInterval(fetchDocs, 2500);
    return () => clearInterval(interval);
  }, [documents, fetchDocs]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    const targetKb = selectedKb || (knowledgeBases.length > 0 ? knowledgeBases[0].id : "");
    if (!files || files.length === 0 || !targetKb) {
      if (!targetKb) alert("Please create or select a Knowledge Base first before uploading.");
      return;
    }
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("knowledge_base_id", targetKb);
        await api.postForm("/documents/upload", formData);
      }
      await fetchDocs();
    } catch (err: unknown) {
      console.error("Upload failed", err);
      const msg = err instanceof Error ? err.message : "Document upload failed";
      alert(`Upload error: ${msg}`);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this document and all indexed chunks?")) return;
    try {
      await api.delete(`/documents/${id}`);
      if (selectedDoc?.id === id) {
        setSelectedDoc(null);
        setChunks([]);
      }
      await fetchDocs();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete document";
      alert(`Delete error: ${msg}`);
    }
  };

  const viewChunks = async (doc: DocType) => {
    setSelectedDoc(doc);
    const data = await api.get<DocumentChunk[]>(`/documents/${doc.id}/chunks`);
    setChunks(data);
  };

  const filtered = documents.filter((d) =>
    d.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-white/[0.06]">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
            Document Hub
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Upload, parse, semantic-chunk, and inspect all knowledge assets.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedKb}
            onChange={(e) => setSelectedKb(e.target.value)}
            className="px-3.5 py-2.5 rounded-xl text-sm font-medium bg-[#141724] border border-white/[0.08] text-slate-200 outline-none focus:border-indigo-500/50"
          >
            <option value="">All Knowledge Bases</option>
            {knowledgeBases.map((kb) => (
              <option key={kb.id} value={kb.id}>
                {kb.name}
              </option>
            ))}
          </select>

          {knowledgeBases.length === 0 ? (
            <a
              href="/knowledge-bases"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 transition-all hover:scale-105"
            >
              <Plus className="w-4 h-4" />
              <span>Create Knowledge Base</span>
            </a>
          ) : (
            <label
              className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold cursor-pointer shadow-md transition-all ${
                uploading
                  ? "bg-indigo-700/60 text-slate-300 cursor-wait"
                  : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/20 hover:scale-105"
              }`}
            >
              {uploading ? (
                <Loader2 className="w-4 h-4 animate-spin text-white" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              <span>Upload Document</span>
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.txt,.md,.csv"
                onChange={handleUpload}
                className="hidden"
                disabled={uploading}
              />
            </label>
          )}
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          placeholder="Filter documents by filename..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm bg-[#141724]/70 border border-white/[0.08] text-slate-200 placeholder:text-slate-400 outline-none focus:border-indigo-500/50"
        />
      </div>

      {/* Document Content Split Layout */}
      <div className="flex gap-8 items-start">
        {/* Document Cards List */}
        <div className={selectedDoc ? "w-1/2" : "w-full"}>
          {loading ? (
            <div className="flex items-center justify-center py-20 text-slate-400">
              <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16 glass-panel rounded-2xl border border-white/[0.06] bg-[#141724]/40">
              <FileText className="w-12 h-12 mx-auto mb-3 text-slate-400" />
              <h3 className="text-base font-bold text-slate-200 mb-1">No documents found</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4">
                {selectedKb
                  ? "Upload a PDF, DOCX, Markdown, or CSV file above to start indexing."
                  : "Select a knowledge base above to view and upload files."}
              </p>
            </div>
          ) : (
            <div className="space-y-3.5">
              {filtered.map((doc) => {
                const Icon = fileIcons[doc.file_type] || FileText;
                const status = statusStyles[doc.status] || statusStyles.UPLOADING;
                const isSelected = selectedDoc?.id === doc.id;

                return (
                  <div
                    key={doc.id}
                    onClick={() => viewChunks(doc)}
                    className={`glass-panel p-5 rounded-2xl border cursor-pointer transition-all ${
                      isSelected
                        ? "border-indigo-500/60 bg-[#181d2e] shadow-md shadow-indigo-500/10"
                        : "border-white/[0.06] bg-[#141724]/70 hover:bg-[#181d2e] hover:border-white/[0.12]"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3.5 min-w-0">
                        <div className="w-10 h-10 rounded-xl bg-white/[0.04] border border-white/[0.06] flex items-center justify-center shrink-0">
                          <Icon className="w-5 h-5 text-indigo-400" />
                        </div>
                        <div className="min-w-0">
                          <div className="text-sm font-bold text-white truncate">
                            {doc.filename}
                          </div>
                          <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                            <span>{formatBytes(doc.file_size)}</span>
                            <span>•</span>
                            <span className="uppercase font-semibold">{doc.file_type}</span>
                            {doc.chunk_count != null && (
                              <>
                                <span>•</span>
                                <span className="text-indigo-300 font-medium">
                                  {doc.chunk_count} chunks
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <span
                          className={`text-xs font-bold px-2.5 py-1 rounded-full border ${status.color} ${status.bg} ${status.border}`}
                        >
                          {doc.status}
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(doc.id);
                          }}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {doc.summary && (
                      <p className="text-xs text-slate-400 mt-3.5 line-clamp-2 leading-relaxed">
                        {doc.summary}
                      </p>
                    )}

                    {doc.topics && doc.topics.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-white/[0.04]">
                        {doc.topics.slice(0, 5).map((t: string) => (
                          <span
                            key={t}
                            className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-white/[0.04] text-slate-300 border border-white/[0.06]"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Side Chunk Inspector Panel */}
        {selectedDoc && (
          <div className="w-1/2 glass-panel p-6 rounded-2xl border border-white/[0.06] bg-[#141724]/90 sticky top-6 max-h-[calc(100vh-12rem)] flex flex-col">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/[0.06] shrink-0">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                <h3 className="text-base font-bold text-white tracking-tight">Chunk Inspector</h3>
              </div>
              <button
                onClick={() => {
                  setSelectedDoc(null);
                  setChunks([]);
                }}
                className="p-1 rounded-lg text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="text-xs text-slate-400 mb-4 shrink-0 font-medium">
              <span className="text-white font-bold">{selectedDoc.filename}</span> • {chunks.length}{" "}
              total indexed chunks
            </div>

            {/* Chunks Scrollable List */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {chunks.map((c) => (
                <div
                  key={c.id}
                  className="p-4 rounded-xl bg-[#0e101a] border border-white/[0.06] space-y-2"
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-mono font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                      Chunk #{c.chunk_index}
                    </span>
                    <div className="flex items-center gap-3 text-slate-400">
                      {c.page_number && <span>Page {c.page_number}</span>}
                      <span>{c.token_count} tokens</span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap">
                    {c.content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function DocumentsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[50vh]">
          <div className="flex items-center gap-3 text-slate-400">
            <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
            <span className="text-sm font-medium">Loading documents...</span>
          </div>
        </div>
      }
    >
      <DocumentsContent />
    </Suspense>
  );
}
