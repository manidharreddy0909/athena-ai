"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  BrainCircuit, Home, MessageSquare, Mic, BarChart2,
  TrendingUp, Zap, ChevronRight, X
} from "lucide-react";
import Link from "next/link";

const NAV_LINKS = [
  { href: "/", label: "Home", icon: Home },
  { href: "/interview", label: "Text Interview", icon: MessageSquare },
  { href: "/interview/video", label: "Video Interview", icon: Zap },
  { href: "/voice", label: "Voice Interview", icon: Mic },
  { href: "/progress", label: "Progress", icon: TrendingUp },
  { href: "/dashboard", label: "Report", icon: BarChart2 },
];

export default function NavBar() {
  const pathname = usePathname();
  const [hasSession, setHasSession] = useState(false);
  const [candidateName, setCandidateName] = useState<string | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const checkSession = () => {
      const sid = localStorage.getItem("athena_session_id");
      const profile = localStorage.getItem("athena_profile");
      setHasSession(!!sid);
      if (profile) {
        try {
          const p = JSON.parse(profile);
          setCandidateName(p.name || null);
        } catch {
          setCandidateName(null);
        }
      }
    };

    checkSession();
    // Poll for session changes
    const interval = setInterval(checkSession, 2000);
    return () => clearInterval(interval);
  }, [pathname]);

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <>
      {/* Desktop Nav */}
      <nav className="hidden md:flex fixed top-0 left-0 right-0 z-50 items-center justify-between px-8 py-4 bg-bg-primary/80 backdrop-blur-xl border-b border-white/5">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="relative w-8 h-8 flex items-center justify-center rounded-lg bg-accent-primary/20 border border-accent-primary/30 group-hover:bg-accent-primary/30 transition-all">
            <BrainCircuit className="w-4.5 h-4.5 text-accent-primary" size={18} />
            {hasSession && (
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-accent-success border-2 border-bg-primary animate-pulse" />
            )}
          </div>
          <span className="font-display font-bold text-lg tracking-tight text-text-primary">
            Athena<span className="text-accent-primary"> AI</span>
          </span>
        </Link>

        {/* Links */}
        <div className="flex items-center gap-1">
          {NAV_LINKS.map(({ href, label, icon: Icon }) => {
            const active = isActive(href);
            return (
              <Link
                key={href}
                href={href}
                className={`relative flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all group ${
                  active
                    ? "text-text-primary"
                    : "text-text-secondary hover:text-text-primary"
                }`}
              >
                {active && (
                  <motion.div
                    layoutId="nav-indicator"
                    className="absolute inset-0 bg-white/8 rounded-lg border border-white/10"
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  />
                )}
                <Icon size={14} className={active ? "text-accent-primary" : "text-text-secondary group-hover:text-text-primary"} />
                <span className="relative z-10">{label}</span>
              </Link>
            );
          })}
        </div>

        {/* Session Badge */}
        <div className="flex items-center gap-3">
          <AnimatePresence>
            {hasSession && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9, x: 10 }}
                animate={{ opacity: 1, scale: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.9, x: 10 }}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent-success/10 border border-accent-success/20 text-xs"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-accent-success animate-pulse" />
                <span className="text-accent-success font-medium">
                  {candidateName ? `${candidateName} · Live` : "Session Active"}
                </span>
              </motion.div>
            )}
          </AnimatePresence>

          <Link
            href="/"
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-accent-primary text-white text-sm font-semibold hover:bg-accent-primary/80 transition-all"
          >
            New Session <ChevronRight size={14} />
          </Link>
        </div>
      </nav>

      {/* Mobile Nav */}
      <nav className="md:hidden fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-5 py-4 bg-bg-primary/90 backdrop-blur-xl border-b border-white/5">
        <Link href="/" className="flex items-center gap-2">
          <BrainCircuit className="text-accent-primary" size={22} />
          <span className="font-display font-bold text-base text-text-primary">Athena AI</span>
        </Link>
        <button
          onClick={() => setMenuOpen(v => !v)}
          className="p-2 rounded-lg bg-white/5 border border-white/10 text-text-secondary hover:text-text-primary transition-all"
        >
          {menuOpen ? <X size={18} /> : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          )}
        </button>
      </nav>

      {/* Mobile Dropdown */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="md:hidden fixed top-[65px] left-0 right-0 z-40 bg-bg-surface/95 backdrop-blur-xl border-b border-white/10 p-4 space-y-1"
          >
            {NAV_LINKS.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                onClick={() => setMenuOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                  isActive(href)
                    ? "bg-accent-primary/20 text-accent-primary border border-accent-primary/30"
                    : "text-text-secondary hover:bg-white/5 hover:text-text-primary"
                }`}
              >
                <Icon size={16} />
                {label}
              </Link>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Spacer to push content below nav */}
      <div className="h-16" />
    </>
  );
}
