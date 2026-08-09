"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, Cell
} from "recharts";
import {
  TrendingUp, TrendingDown, Minus, Brain, Target, Zap,
  BookOpen, Trophy, ChevronRight, ArrowRight, RefreshCw,
  BarChart2, CheckCircle, XCircle, Flame
} from "lucide-react";
import { api } from "@/lib/api";
import Link from "next/link";

interface DigitalTwin {
  candidate_name: string;
  sessions_count: number;
  skill_vector: Record<string, number>;
  topic_practice_count: Record<string, number>;
  growth_trajectory: {
    trend: string;
    sessions_count: number;
    first_score?: number;
    latest_score?: number;
    improvement_delta?: number;
    scores_over_time?: number[];
    average_score?: number;
  };
  weak_topics: string[];
  strong_topics: string[];
  recommended_domains: string[];
  dimension_history: Array<{
    timestamp: number;
    session_id: string;
    domain: string;
    scores: Record<string, number>;
    overall: number;
  }>;
}

interface CandidateHistory {
  candidate_name: string;
  total_sessions: number;
  sessions: Array<{
    session_id: string;
    domain: string;
    mode: string;
    questions_asked: number;
    topics_covered: string[];
    status: string;
    confidence_score: number;
    avg_score: number;
  }>;
}

const SCORE_COLOR = (score: number) =>
  score >= 75 ? "#10b981" : score >= 55 ? "#f59e0b" : "#ef4444";

const TREND_ICON = {
  improving: TrendingUp,
  declining: TrendingDown,
  stable: Minus,
  baseline: Target,
  no_data: BarChart2,
};

const TREND_COLOR = {
  improving: "text-accent-success",
  declining: "text-accent-danger",
  stable: "text-accent-warning",
  baseline: "text-accent-secondary",
  no_data: "text-text-secondary",
};

export default function ProgressPage() {
  const router = useRouter();
  const [twin, setTwin] = useState<DigitalTwin | null>(null);
  const [history, setHistory] = useState<CandidateHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [candidateName, setCandidateName] = useState<string>("Unknown");

  const fetchData = useCallback(async (name: string) => {
    setLoading(true);
    setError(null);
    try {
      const [twinData, histData] = await Promise.allSettled([
        api.getDigitalTwin(name),
        api.getCandidateHistory(name),
      ]);
      if (twinData.status === "fulfilled") setTwin(twinData.value);
      if (histData.status === "fulfilled") setHistory(histData.value);
      if (twinData.status === "rejected" && histData.status === "rejected") {
        setError("No progress data found. Complete at least one interview to see your progress.");
      }
    } catch {
      setError("Could not load progress data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const profileStr = localStorage.getItem("athena_profile");
    let name = "Unknown";
    if (profileStr) {
      try {
        const profile = JSON.parse(profileStr);
        name = profile.name || "Unknown";
      } catch {}
    }
    setCandidateName(name);
    fetchData(name);
  }, [fetchData]);

  const trendKey = (twin?.growth_trajectory?.trend || "no_data") as keyof typeof TREND_ICON;
  const TrendIcon = TREND_ICON[trendKey] || BarChart2;
  const trendColorClass = TREND_COLOR[trendKey] || "text-text-secondary";

  const sessionChartData = twin?.growth_trajectory?.scores_over_time?.map((score, i) => ({
    session: `S${i + 1}`,
    score,
  })) || [];

  const skillChartData = Object.entries(twin?.skill_vector || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([topic, conf]) => ({
      topic: topic.length > 15 ? topic.slice(0, 14) + "…" : topic,
      fullTopic: topic,
      score: Math.round(conf * 100),
    }));

  const radarData = Object.entries(twin?.skill_vector || {})
    .slice(0, 6)
    .map(([topic, conf]) => ({
      subject: topic.length > 12 ? topic.slice(0, 11) + "…" : topic,
      A: Math.round(conf * 100),
      fullMark: 100,
    }));

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="relative mx-auto w-16 h-16">
            <div className="absolute inset-0 rounded-full border-2 border-accent-primary/30 animate-ping" />
            <div className="absolute inset-2 rounded-full bg-accent-primary/20 animate-pulse" />
            <Brain className="absolute inset-0 m-auto text-accent-primary" size={28} />
          </div>
          <p className="text-text-secondary font-mono text-sm animate-pulse">
            Loading Digital Twin Profile…
          </p>
        </div>
      </div>
    );
  }

  if (error && !twin && !history) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-panel p-10 max-w-lg text-center space-y-6"
        >
          <div className="w-20 h-20 rounded-full bg-accent-primary/10 border border-accent-primary/30 flex items-center justify-center mx-auto">
            <Brain className="text-accent-primary" size={36} />
          </div>
          <div>
            <h2 className="text-2xl font-bold font-display mb-2">No Progress Yet</h2>
            <p className="text-text-secondary text-sm leading-relaxed">{error}</p>
          </div>
          <div className="flex gap-3 justify-center">
            <Link
              href="/"
              className="flex items-center gap-2 px-6 py-3 bg-accent-primary text-white rounded-xl font-semibold hover:bg-accent-primary/80 transition-all"
            >
              Start Interview <ChevronRight size={16} />
            </Link>
            <button
              onClick={() => fetchData(candidateName)}
              className="flex items-center gap-2 px-4 py-3 bg-white/10 text-text-primary rounded-xl hover:bg-white/20 transition-all"
            >
              <RefreshCw size={16} /> Retry
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
      >
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center">
              <Brain size={20} className="text-white" />
            </div>
            <h1 className="text-3xl font-bold font-display text-text-primary">
              Digital Twin
            </h1>
          </div>
          <p className="text-text-secondary text-sm ml-13">
            Candidate:{" "}
            <span className="text-text-primary font-semibold">{candidateName}</span>
            {twin && (
              <span className="ml-3 text-xs text-text-secondary">
                · {twin.sessions_count} session{twin.sessions_count !== 1 ? "s" : ""} tracked
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => fetchData(candidateName)}
            className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl text-sm transition-all"
          >
            <RefreshCw size={14} /> Refresh
          </button>
          <Link
            href="/"
            className="flex items-center gap-2 px-5 py-2 bg-accent-primary hover:bg-accent-primary/80 text-white rounded-xl text-sm font-semibold transition-all"
          >
            Practice Now <ArrowRight size={14} />
          </Link>
        </div>
      </motion.header>

      {/* Growth Trajectory Hero */}
      {twin && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="glass-panel p-6 grid grid-cols-2 md:grid-cols-4 gap-6"
        >
          {/* Trend */}
          <div className="flex flex-col items-center justify-center text-center p-4 rounded-xl bg-white/4 border border-white/8">
            <TrendIcon size={32} className={`mb-2 ${trendColorClass}`} />
            <div className={`text-lg font-bold uppercase ${trendColorClass}`}>
              {twin.growth_trajectory.trend?.replace("_", " ")}
            </div>
            <div className="text-xs text-text-secondary mt-1">Performance Trend</div>
          </div>

          {/* Sessions */}
          <div className="flex flex-col items-center justify-center text-center p-4 rounded-xl bg-white/4 border border-white/8">
            <div className="text-4xl font-bold text-accent-secondary mb-1">
              {twin.sessions_count}
            </div>
            <div className="text-xs text-text-secondary">Sessions Completed</div>
          </div>

          {/* Avg Score */}
          <div className="flex flex-col items-center justify-center text-center p-4 rounded-xl bg-white/4 border border-white/8">
            <div
              className="text-4xl font-bold mb-1"
              style={{ color: SCORE_COLOR(twin.growth_trajectory.average_score || 0) }}
            >
              {twin.growth_trajectory.average_score ?? "—"}
            </div>
            <div className="text-xs text-text-secondary">Average Score</div>
          </div>

          {/* Improvement */}
          <div className="flex flex-col items-center justify-center text-center p-4 rounded-xl bg-white/4 border border-white/8">
            <div
              className="text-4xl font-bold mb-1"
              style={{
                color:
                  (twin.growth_trajectory.improvement_delta || 0) >= 0
                    ? "#10b981"
                    : "#ef4444",
              }}
            >
              {twin.growth_trajectory.improvement_delta !== undefined
                ? `${(twin.growth_trajectory.improvement_delta || 0) >= 0 ? "+" : ""}${twin.growth_trajectory.improvement_delta}`
                : "—"}
            </div>
            <div className="text-xs text-text-secondary">Score Improvement</div>
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Score Over Time Chart */}
        {sessionChartData.length > 0 && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-2 glass-panel p-6"
          >
            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <TrendingUp className="text-accent-primary" size={18} />
              Score Over Time
            </h2>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={sessionChartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <XAxis
                    dataKey="session"
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[0, 100]}
                    tick={{ fill: "#94a3b8", fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "#12121a",
                      border: "1px solid rgba(255,255,255,0.1)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    labelStyle={{ color: "#f8fafc" }}
                    formatter={(v: any) => [`${v}`, "Score"]}
                  />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#7c3aed"
                    strokeWidth={2.5}
                    dot={{ fill: "#7c3aed", r: 4, strokeWidth: 0 }}
                    activeDot={{ r: 6, fill: "#06b6d4" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        )}

        {/* Skill Radar */}
        {radarData.length > 0 && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.25 }}
            className="glass-panel p-6 flex flex-col items-center"
          >
            <h2 className="text-lg font-semibold mb-4 w-full flex items-center gap-2">
              <Target className="text-accent-secondary" size={18} />
              Skill Radar
            </h2>
            <div className="w-full h-48">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="65%" data={radarData}>
                  <PolarGrid stroke="rgba(255,255,255,0.1)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: "#94a3b8", fontSize: 9 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar name="Skill" dataKey="A" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.25} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Topic Mastery Bar Chart */}
        {skillChartData.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-2 glass-panel p-6"
          >
            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <BarChart2 className="text-accent-warning" size={18} />
              Topic Mastery
            </h2>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={skillChartData} layout="vertical" margin={{ left: 10, right: 20 }}>
                  <XAxis type="number" domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="topic" tick={{ fill: "#94a3b8", fontSize: 10 }} axisLine={false} tickLine={false} width={90} />
                  <Tooltip
                    contentStyle={{ background: "#12121a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                    formatter={(v: any, _: any, props: any) => [`${v}%`, props?.payload?.fullTopic]}
                  />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                    {skillChartData.map((entry, i) => (
                      <Cell key={i} fill={SCORE_COLOR(entry.score)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        )}

        {/* Weak / Strong Topics */}
        {twin && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="glass-panel p-6 space-y-5"
          >
            {/* Strong */}
            <div>
              <h3 className="text-sm font-bold text-accent-success uppercase tracking-wider mb-3 flex items-center gap-2">
                <Trophy size={14} /> Mastered
              </h3>
              <div className="space-y-1.5">
                {twin.strong_topics.slice(0, 4).map((t, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <CheckCircle size={13} className="text-accent-success shrink-0" />
                    <span className="text-text-primary">{t}</span>
                  </div>
                ))}
                {twin.strong_topics.length === 0 && (
                  <p className="text-text-secondary text-xs italic">Keep practicing to master topics!</p>
                )}
              </div>
            </div>

            {/* Weak */}
            <div>
              <h3 className="text-sm font-bold text-accent-danger uppercase tracking-wider mb-3 flex items-center gap-2">
                <Flame size={14} /> Focus Areas
              </h3>
              <div className="space-y-1.5">
                {twin.weak_topics.slice(0, 4).map((t, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <XCircle size={13} className="text-accent-danger shrink-0" />
                    <span className="text-text-primary">{t}</span>
                  </div>
                ))}
                {twin.weak_topics.length === 0 && (
                  <p className="text-text-secondary text-xs italic">No weak areas identified yet.</p>
                )}
              </div>
            </div>

            {/* CTA */}
            {twin.weak_topics.length > 0 && (
              <Link
                href="/"
                className="flex items-center justify-center gap-2 w-full py-2.5 mt-2 bg-accent-primary/20 hover:bg-accent-primary/30 border border-accent-primary/40 text-accent-primary rounded-xl text-sm font-semibold transition-all"
              >
                Practice Weak Areas <ChevronRight size={14} />
              </Link>
            )}
          </motion.div>
        )}
      </div>

      {/* Session History */}
      {history && history.sessions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass-panel p-6"
        >
          <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
            <BookOpen className="text-accent-secondary" size={18} />
            Session History
          </h2>
          <div className="space-y-3">
            {history.sessions.map((session, i) => (
              <motion.div
                key={session.session_id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.05 }}
                className="flex items-center gap-4 p-4 rounded-xl bg-white/4 border border-white/8 hover:border-white/15 transition-all"
              >
                <div className="w-10 h-10 rounded-lg bg-bg-surface border border-white/10 flex items-center justify-center font-mono text-sm font-bold text-accent-primary shrink-0">
                  S{i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-text-primary capitalize">{session.domain?.replace("_", " ")}</span>
                    <span className="text-xs px-2 py-0.5 bg-white/5 rounded-full text-text-secondary">{session.mode}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${session.status === "complete" ? "bg-accent-success/20 text-accent-success" : "bg-accent-warning/20 text-accent-warning"}`}>
                      {session.status}
                    </span>
                  </div>
                  <div className="text-xs text-text-secondary">
                    {session.questions_asked} questions · Topics: {session.topics_covered.slice(0, 3).join(", ")}{session.topics_covered.length > 3 ? "…" : ""}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div
                    className="text-xl font-bold"
                    style={{ color: SCORE_COLOR(session.avg_score * 100) }}
                  >
                    {Math.round(session.avg_score * 100)}%
                  </div>
                  <div className="text-xs text-text-secondary">avg score</div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
