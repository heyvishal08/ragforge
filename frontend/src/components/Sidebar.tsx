"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Database,
  FileText,
  MessageSquare,
  Search,
  FlaskConical,
  BarChart3,
  Settings,
  Zap,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/knowledge-bases", label: "Knowledge Bases", icon: Database },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/chat", label: "Research Chat", icon: MessageSquare, badge: "Live" },
  { href: "/playground", label: "Retrieval Playground", icon: Search },
  { href: "/evaluations", label: "Evaluations", icon: FlaskConical },
  { href: "/analytics", label: "Observability", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 shrink-0 h-screen sticky top-0 flex flex-col bg-[#0c0e17] border-r border-white/[0.07] z-30 select-none">
      {/* Brand Header */}
      <div className="h-20 flex items-center px-6 border-b border-white/[0.06] shrink-0">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl glow-gradient flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
              RAGForge
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                v1.0
              </span>
            </div>
            <div className="text-[11px] font-medium text-slate-400">Evidence-First AI</div>
          </div>
        </Link>
      </div>

      {/* Nav List */}
      <div className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-3 mb-3">
          Platform
        </div>

        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group relative",
                isActive
                  ? "bg-indigo-600/15 text-white font-semibold shadow-sm border border-indigo-500/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]"
              )}
            >
              <div className="flex items-center gap-3">
                <item.icon
                  className={cn(
                    "w-4 h-4 transition-colors",
                    isActive ? "text-indigo-400" : "text-slate-400 group-hover:text-slate-300"
                  )}
                />
                <span>{item.label}</span>
              </div>

              {item.badge && (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      {/* Footer Info Box */}
      <div className="p-4 border-t border-white/[0.06] shrink-0">
        <div className="p-3.5 rounded-xl bg-gradient-to-br from-indigo-950/40 to-slate-900/60 border border-indigo-500/20 flex items-start gap-3">
          <Sparkles className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
          <div className="text-xs">
            <div className="font-semibold text-slate-200">Groq LPU Enabled</div>
            <div className="text-[11px] text-slate-400 mt-0.5">qwen/qwen3.8-27b</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
