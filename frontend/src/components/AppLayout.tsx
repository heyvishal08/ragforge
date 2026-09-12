"use client";

import Sidebar from "@/components/Sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      suppressHydrationWarning
      className="flex min-h-screen bg-[#090a0f] text-slate-100 antialiased selection:bg-indigo-500/30 selection:text-white"
    >
      <Sidebar />
      <main className="flex-1 min-w-0 flex flex-col min-h-screen overflow-x-hidden">
        <div className="flex-1 w-full max-w-7xl mx-auto px-6 py-8 md:px-10 md:py-10">
          {children}
        </div>
      </main>
    </div>
  );
}
