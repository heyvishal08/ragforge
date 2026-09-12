import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RAGForge — Evidence-first AI Knowledge Engine",
  description:
    "Ask questions across your documents and see exactly where every answer comes from. Multi-document AI knowledge platform with hybrid retrieval, citations, and evaluation.",
  keywords: [
    "RAG",
    "retrieval augmented generation",
    "AI knowledge base",
    "document Q&A",
    "hybrid search",
    "citations",
    "evidence-based AI",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="min-h-screen antialiased" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
