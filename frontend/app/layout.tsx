import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import NavBar from "@/components/NavBar";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Athena AI — Autonomous Interview Intelligence Platform",
  description:
    "AI-powered adaptive technical interviews with explainable reasoning, knowledge graphs, and recruiter intelligence reports.",
  keywords: ["AI interview", "technical interview", "adaptive AI", "LangGraph", "RAG"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-[#0a0a0f] text-[#f8fafc] antialiased min-h-screen">
        <NavBar />
        {children}
      </body>
    </html>
  );
}
