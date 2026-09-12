"use client";

import { useEffect, useState } from "react";
import { Database, Plus, Trash2, FileText, ArrowRight, X, Sparkles } from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import type { KnowledgeBase } from "@/types";
import { formatDate } from "@/lib/utils";

export default function KnowledgeBasesPage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");

  const fetchKBs = async () => {
    try {
      const data = await api.get<KnowledgeBase[]>("/knowledge-bases");
      setKnowledgeBases(data);
    } catch {
      console.error("Failed to fetch knowledge bases");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKBs();
  }, []);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      await api.post("/knowledge-bases", { name: newName, description: newDesc || null });
      setNewName("");
      setNewDesc("");
      setCreating(false);
      fetchKBs();
    } catch (err) {
      console.error("Failed to create knowledge base", err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this knowledge base and all its documents?")) return;
    try {
      await api.delete(`/knowledge-bases/${id}`);
      fetchKBs();
    } catch (err) {
      console.error("Failed to delete knowledge base", err);
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-white/[0.06]">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
            Knowledge Bases
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Isolate and organize your documents into custom research domains.
          </p>
        </div>

        <button
          onClick={() => setCreating(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 transition-all hover:scale-105"
        >
          <Plus className="w-4 h-4" />
          Create Knowledge Base
        </button>
      </div>

      {/* Creation Modal/Drawer */}
      {creating && (
        <div className="glass-panel p-6 rounded-2xl border border-indigo-500/30 bg-[#181d2e] shadow-xl space-y-4 max-w-xl">
          <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
            <h3 className="text-base font-bold text-white tracking-tight">New Knowledge Base</h3>
            <button
              onClick={() => setCreating(false)}
              className="p-1 rounded-lg text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1">Name</label>
              <input
                type="text"
                placeholder="e.g. Legal Contracts 2024"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl text-sm bg-[#141724] border border-white/[0.08] text-white outline-none focus:border-indigo-500/60"
                autoFocus
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1">
                Description (Optional)
              </label>
              <input
                type="text"
                placeholder="Brief summary of topics or domain"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl text-sm bg-[#141724] border border-white/[0.08] text-white outline-none focus:border-indigo-500/60"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              onClick={() => setCreating(false)}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={handleCreate}
              className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/25"
            >
              Save Knowledge Base
            </button>
          </div>
        </div>
      )}

      {/* Grid of Knowledge Bases */}
      {loading ? (
        <div className="text-center py-20 text-slate-400">Loading knowledge bases...</div>
      ) : knowledgeBases.length === 0 ? (
        <div className="text-center py-16 glass-panel rounded-2xl border border-white/[0.06] bg-[#141724]/40">
          <Database className="w-12 h-12 mx-auto mb-3 text-slate-400" />
          <h3 className="text-base font-bold text-white mb-1">No knowledge bases yet</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mb-6">
            Create your first domain to start organizing and asking questions over your files.
          </p>
          <button
            onClick={() => setCreating(true)}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500 shadow-md shadow-indigo-600/20"
          >
            <Plus className="w-3.5 h-3.5" />
            Create Knowledge Base
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {knowledgeBases.map((kb) => (
            <div
              key={kb.id}
              className="glass-panel p-6 rounded-2xl border border-white/[0.06] bg-[#141724]/70 hover:bg-[#181d2e] hover:border-white/[0.12] transition-all flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-start justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                    <Database className="w-5 h-5 text-indigo-400" />
                  </div>
                  <button
                    onClick={() => handleDelete(kb.id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <h3 className="text-base font-bold text-white tracking-tight mb-1.5">{kb.name}</h3>
                {kb.description && (
                  <p className="text-xs text-slate-400 leading-relaxed line-clamp-2 mb-4">
                    {kb.description}
                  </p>
                )}
              </div>

              <div className="pt-4 border-t border-white/[0.06] mt-4 space-y-4">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center gap-1.5 font-medium text-slate-300">
                    <FileText className="w-3.5 h-3.5 text-indigo-400" />
                    {kb.document_count} doc{kb.document_count !== 1 ? "s" : ""}
                  </span>
                  <span>{formatDate(kb.created_at)}</span>
                </div>

                <div className="grid grid-cols-2 gap-2.5">
                  <Link
                    href={`/chat?kb=${kb.id}`}
                    className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm transition-colors"
                  >
                    Chat <ArrowRight className="w-3 h-3" />
                  </Link>
                  <Link
                    href={`/documents?kb=${kb.id}`}
                    className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-white/[0.05] hover:bg-white/[0.08] text-slate-300 border border-white/[0.06] transition-colors"
                  >
                    Documents
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
