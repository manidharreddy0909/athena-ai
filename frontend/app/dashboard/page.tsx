"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from "recharts";
import {
  Brain, TrendingUp, CheckCircle, XCircle, Download, Star,
  Calendar, BarChart2, BookOpen, ArrowLeft, Flag, Info
} from "lucide-react";
import { api, FeedbackReport } from "@/lib/api";

const HIRE_COLORS: Record<string, string> = {
  strong_hire: "#10b981", // Emerald
  hire: "#06b6d4",        // Cyan
  consider: "#f59e0b",    // Amber
  no_hire: "#ef4444",     // Red
};

const SCORE_COLOR = (score: number) =>
  score >= 75 ? "#10b981" : score >= 55 ? "#f59e0b" : "#ef4444";

export default function DashboardPage() {
  const router = useRouter();
  const [report, setReport] = useState<FeedbackReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const sessionId = localStorage.getItem("athena_session_id");
    if (!sessionId) {
      router.push("/");
      return;
    }

    api.getReport(sessionId)
      .then(setReport)
      .catch((err) => {
        console.error(err);
        setError("Failed to load report. The interview may not be complete yet.");
      })
      .finally(() => setLoading(false));
  }, [router]);

  const handleExport = useCallback(() => {
    window.print();
  }, []);

  const handleNewInterview = useCallback(() => {
    localStorage.removeItem("athena_session_id");
    localStorage.removeItem("athena_session_data");
    router.push("/");
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="relative mx-auto w-16 h-16">
            <div className="absolute inset-0 rounded-full border-2 border-accent-primary/30 animate-ping" />
            <div className="absolute inset-2 rounded-full bg-accent-primary/20 animate-pulse" />
            <Brain className="absolute inset-0 m-auto text-accent-primary" size={32} />
          </div>
          <p className="text-text-secondary animate-pulse font-mono text-sm">
            Compiling Recruiter Intelligence Report...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="glass-panel p-8 max-w-md text-center space-y-4">
          <XCircle className="mx-auto text-accent-danger" size={48} />
          <h2 className="text-xl font-bold">Report Unavailable</h2>
          <p className="text-text-secondary text-sm">{error}</p>
          <button
            onClick={() => router.push("/")}
            className="px-6 py-2 bg-accent-primary text-white rounded-lg flex items-center gap-2 mx-auto"
          >
            <ArrowLeft size={16} /> Back to Start
          </button>
        </div>
      </div>
    );
  }

  if (!report) return null;

  const radarData = [
    { subject: "Technical", A: report.technical_depth.score, fullMark: 100 },
    { subject: "Coding", A: report.coding_ability.score, fullMark: 100 },
    { subject: "Architecture", A: report.architecture.score, fullMark: 100 },
    { subject: "Reasoning", A: report.reasoning.score, fullMark: 100 },
    { subject: "Communication", A: report.communication.score, fullMark: 100 },
  ];

  const barData = [
    { name: "Technical", score: report.technical_depth.score },
    { name: "Coding", score: report.coding_ability.score },
    { name: "Architecture", score: report.architecture.score },
    { name: "Reasoning", score: report.reasoning.score },
    { name: "Communication", score: report.communication.score },
  ];

  const hireColor = HIRE_COLORS[report.hiring_recommendation] || "#94a3b8";
  const overallScore = Math.round(report.overall_score);

  return (
    <>
      {/* Print styles */}
      <style>{`
        @media print {
          body { background: white !important; color: black !important; }
          .no-print { display: none !important; }
          .glass-panel { border: 1px solid #e2e8f0 !important; background: white !important; }
        }
      `}</style>

      <div className="min-h-screen p-4 md:p-8 max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <motion.header
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
        >
          <div>
            <h1 className="text-3xl font-bold font-display text-text-primary">
              Recruiter Intelligence Report
            </h1>
            <p className="text-text-secondary mt-1">
              Candidate: <span className="text-text-primary font-semibold">{report.candidate_name}</span>
              <span className="mx-2 text-white/20">•</span>
              Session: <span className="font-mono text-xs">{report.session_id.substring(0, 16)}</span>
            </p>
          </div>
          <div className="flex items-center gap-3 no-print">
            <button
              onClick={handleNewInterview}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg flex items-center gap-2 transition-colors text-sm"
            >
              <ArrowLeft size={16} /> New Interview
            </button>
            <button
              onClick={handleExport}
              className="px-4 py-2 bg-accent-primary hover:bg-accent-primary/80 text-white rounded-lg flex items-center gap-2 transition-colors text-sm"
            >
              <Download size={16} /> Export PDF
            </button>
          </div>
        </motion.header>

        {/* Score Hero */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="glass-panel p-6 flex flex-wrap items-center gap-6"
        >
          {/* Overall Score Ring */}
          <div className="relative w-28 h-28 flex-shrink-0">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="8" />
              <circle
                cx="50" cy="50" r="45" fill="none"
                stroke={hireColor}
                strokeWidth="8"
                strokeDasharray={`${2 * Math.PI * 45}`}
                strokeDashoffset={`${2 * Math.PI * 45 * (1 - overallScore / 100)}`}
                strokeLinecap="round"
                className="transition-all duration-1000"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold" style={{ color: hireColor }}>{overallScore}</span>
              <span className="text-xs text-text-secondary">/100</span>
            </div>
          </div>

          <div className="flex-1 min-w-48">
            <div
              className="text-2xl font-bold uppercase mb-1"
              style={{ color: hireColor }}
            >
              {report.hiring_recommendation.replace(/_/g, " ")}
            </div>
            <div className="text-text-secondary text-sm mb-3">
              Hiring Confidence: <span className="text-text-primary font-semibold uppercase">{report.hiring_confidence}</span>
            </div>
            <div className="flex flex-wrap gap-4 text-sm text-text-secondary">
              <div className="flex items-center gap-1">
                <BarChart2 size={14} className="text-accent-primary" />
                {report.total_questions} questions
              </div>
              <div className="flex items-center gap-1">
                <Calendar size={14} className="text-accent-secondary" />
                {report.curriculum_days_covered.length} curriculum days
              </div>
              <div className="flex items-center gap-1">
                <BookOpen size={14} className="text-accent-warning" />
                {report.topics_covered.length} topics covered
              </div>
            </div>
          </div>

          {/* Score bars */}
          <div className="w-full md:w-64 h-32 hidden md:block">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ background: '#12121a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                  labelStyle={{ color: '#f8fafc' }}
                  formatter={(v: number) => [`${v}`, 'Score']}
                />
                <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                  {barData.map((entry, i) => (
                    <Cell key={i} fill={SCORE_COLOR(entry.score)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* RECRUITER INTELLIGENCE */}
        {report.executive_summary && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
          >
            <div className="md:col-span-2 glass-panel p-6 border border-accent-secondary/30 bg-accent-secondary/5">
              <h3 className="text-lg font-bold mb-3 flex items-center gap-2 text-accent-secondary">
                <Info size={20} /> Executive Summary
              </h3>
              <p className="text-text-secondary leading-relaxed text-sm">
                {report.executive_summary}
              </p>
              
              {report.culture_fit_notes && (
                <div className="mt-4 pt-4 border-t border-white/10">
                  <h4 className="text-sm font-bold text-text-primary mb-2">Culture Fit Analysis</h4>
                  <p className="text-text-secondary text-sm">{report.culture_fit_notes}</p>
                </div>
              )}
            </div>

            <div className="space-y-6">
              {report.red_flags && report.red_flags.length > 0 && (
                <div className="glass-panel p-5 border border-accent-danger/30 bg-accent-danger/5">
                  <h4 className="text-sm font-bold text-accent-danger mb-3 flex items-center gap-2">
                    <Flag size={16} /> Critical Red Flags
                  </h4>
                  <ul className="space-y-2 text-sm text-text-secondary">
                    {report.red_flags.map((flag, i) => (
                      <li key={i} className="flex gap-2"><XCircle size={14} className="text-accent-danger mt-0.5 shrink-0" /> <span>{flag}</span></li>
                    ))}
                  </ul>
                </div>
              )}
              {report.green_flags && report.green_flags.length > 0 && (
                <div className="glass-panel p-5 border border-accent-success/30 bg-accent-success/5">
                  <h4 className="text-sm font-bold text-accent-success mb-3 flex items-center gap-2">
                    <Star size={16} /> Notable Strengths
                  </h4>
                  <ul className="space-y-2 text-sm text-text-secondary">
                    {report.green_flags.map((flag, i) => (
                      <li key={i} className="flex gap-2"><CheckCircle size={14} className="text-accent-success mt-0.5 shrink-0" /> <span>{flag}</span></li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </motion.div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Left: Radar Chart */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-panel p-6 flex flex-col items-center"
          >
            <h2 className="text-lg font-semibold w-full mb-4 flex items-center gap-2">
              <Star className="text-accent-primary" size={18} /> Skill Analysis
            </h2>
            <div className="w-full h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                  <PolarGrid stroke="rgba(255,255,255,0.1)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar name="Candidate" dataKey="A" stroke="#7c3aed" fill="#7c3aed" fillOpacity={0.35} />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            <div className="w-full mt-4 space-y-2">
              {barData.map((item) => (
                <div key={item.name} className="flex items-center gap-3">
                  <span className="text-xs text-text-secondary w-24 flex-shrink-0">{item.name}</span>
                  <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full rounded-full"
                      style={{ backgroundColor: SCORE_COLOR(item.score) }}
                      initial={{ width: 0 }}
                      animate={{ width: `${item.score}%` }}
                      transition={{ duration: 0.8, delay: 0.4 }}
                    />
                  </div>
                  <span className="text-xs font-mono w-8 text-right" style={{ color: SCORE_COLOR(item.score) }}>
                    {item.score}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Middle: Strengths & Weaknesses */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-panel p-6 space-y-6"
          >
            <div>
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-accent-success">
                <CheckCircle size={18} /> Verified Strengths
              </h2>
              <ul className="space-y-2">
                {report.strong_areas.map((area, i) => (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + i * 0.05 }}
                    className="text-sm bg-accent-success/10 border border-accent-success/20 px-3 py-2 rounded-lg text-text-primary flex items-start gap-2"
                  >
                    <CheckCircle className="text-accent-success shrink-0 mt-0.5" size={14} />
                    {area}
                  </motion.li>
                ))}
                {report.strong_areas.length === 0 && (
                  <li className="text-sm text-text-secondary italic">Not enough data to confirm strengths.</li>
                )}
              </ul>
            </div>

            <div>
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-accent-danger">
                <XCircle size={18} /> Knowledge Gaps
              </h2>
              <ul className="space-y-2">
                {report.weak_areas.map((area, i) => (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + i * 0.05 }}
                    className="text-sm bg-accent-danger/10 border border-accent-danger/20 px-3 py-2 rounded-lg text-text-primary flex items-start gap-2"
                  >
                    <XCircle className="text-accent-danger shrink-0 mt-0.5" size={14} />
                    {area}
                  </motion.li>
                ))}
                {report.weak_areas.length === 0 && (
                  <li className="text-sm text-text-secondary italic">No significant gaps identified.</li>
                )}
              </ul>
            </div>
            
            <div>
              <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-3">
                Topics Covered
              </h2>
              <div className="flex flex-wrap gap-2">
                {report.topics_covered.map((t, i) => (
                  <span key={i} className="text-xs px-2 py-1 bg-white/5 rounded-full border border-white/10 text-text-secondary">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Right: Learning Roadmap */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="glass-panel p-6"
          >
            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <TrendingUp className="text-accent-warning" size={18} /> Personalized Roadmap
            </h2>
            
            <div className="space-y-6">
              {/* 30 Day */}
              <div className="relative pl-8">
                <div className="absolute left-0 top-1 w-7 h-7 rounded-full border-2 border-accent-primary bg-bg-surface flex items-center justify-center text-xs font-bold text-accent-primary z-10">
                  30
                </div>
                <div className="absolute left-3.5 top-8 bottom-0 w-px bg-gradient-to-b from-accent-primary/40 to-transparent" />
                <div>
                  <h3 className="font-bold text-text-primary text-sm mb-2">Foundation Repair</h3>
                  <ul className="text-xs text-text-secondary space-y-1.5 list-none">
                    {report.learning_plan_30_day.slice(0, 3).map((item, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-accent-primary mt-0.5">→</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* 60 Day */}
              <div className="relative pl-8">
                <div className="absolute left-0 top-1 w-7 h-7 rounded-full border-2 border-accent-secondary bg-bg-surface flex items-center justify-center text-xs font-bold text-accent-secondary z-10">
                  60
                </div>
                <div className="absolute left-3.5 top-8 bottom-0 w-px bg-gradient-to-b from-accent-secondary/40 to-transparent" />
                <div>
                  <h3 className="font-bold text-text-primary text-sm mb-2">Applied Skills</h3>
                  <ul className="text-xs text-text-secondary space-y-1.5 list-none">
                    {report.learning_plan_60_day.slice(0, 3).map((item, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-accent-secondary mt-0.5">→</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* 90 Day */}
              <div className="relative pl-8">
                <div className="absolute left-0 top-1 w-7 h-7 rounded-full border-2 border-accent-success bg-bg-surface flex items-center justify-center text-xs font-bold text-accent-success z-10">
                  90
                </div>
                <div>
                  <h3 className="font-bold text-text-primary text-sm mb-2">Production Scale</h3>
                  <ul className="text-xs text-text-secondary space-y-1.5 list-none">
                    {report.learning_plan_90_day.slice(0, 3).map((item, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-accent-success mt-0.5">→</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Knowledge Graph Snapshot */}
        {Object.keys(report.knowledge_graph_snapshot).length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="glass-panel p-6"
          >
            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <Brain className="text-accent-primary" size={18} /> Knowledge Graph Snapshot
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {Object.entries(report.knowledge_graph_snapshot).map(([topic, confidence], i) => (
                <motion.div
                  key={topic}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.5 + i * 0.03 }}
                  className="relative p-3 rounded-xl border text-center"
                  style={{
                    borderColor: `${SCORE_COLOR(confidence * 100)}40`,
                    backgroundColor: `${SCORE_COLOR(confidence * 100)}10`,
                  }}
                >
                  <div className="text-xs font-medium text-text-primary mb-1 leading-tight">{topic}</div>
                  <div className="text-lg font-bold" style={{ color: SCORE_COLOR(confidence * 100) }}>
                    {Math.round(confidence * 100)}%
                  </div>
                  <div className="w-full h-1 rounded-full bg-white/10 mt-2 overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${confidence * 100}%`,
                        backgroundColor: SCORE_COLOR(confidence * 100),
                      }}
                    />
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </>
  );
}
