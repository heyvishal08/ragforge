import type { Metadata } from "next";
import AppLayout from "@/components/AppLayout";

export const metadata: Metadata = {
  title: "Dashboard — RAGForge",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <AppLayout>{children}</AppLayout>;
}
