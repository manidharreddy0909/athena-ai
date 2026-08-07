"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";
import { Brain, TrendingUp, CheckCircle, XCircle, FileText, Download } from "lucide-react";
import { api, FeedbackReport } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [report, setReport] = useState<FeedbackReport | null>(null);
  const [loading, setLoading] = useState(true);

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
        alert("Failed to load report. Ensure the interview is complete.");
        router.push("/");
      })
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-xl text-accent-primary font-mono">Compiling Recruiter Intelligence Report...</div>
      </div>
    );
  }

  if (!report) return null;

  const radarData = [
    { subject: 'Technical', A: report.technical_depth.score, fullMark: 100 },
    { subject: 'Coding', A: report.coding_ability.score, fullMark: 100 },
    { subject: 'Architecture', A: report.architecture.score, fullMark: 100 },
    { subject: 'Reasoning', A: report.reasoning.score, fullMark: 100 },
    { subject: 'Communication', A: report.communication.score, fullMark: 100 },
  ];

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-7xl mx-auto space-y-8">
      
      {/* Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold font-display text-text-primary">Recruiter Intelligence Report</h1>
          <p className="text-text-secondary">Candidate: {report.candidate_name} • Session: {report.session_id.substring(0, 12)}</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="px-4 py-2 glass-panel flex items-center gap-2">
            <span className="text-text-secondary text-sm uppercase">Overall Score</span>
            <span className="text-2xl font-bold text-accent-primary">{Math.round(report.overall_score)}</span>
          </div>
          <button className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg flex items-center gap-2 transition-colors">
            <Download size={18} /> Export PDF
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Left Column: Skill Radar */}
        <div className="glass-panel p-6 flex flex-col items-center">
          <h2 className="text-lg font-semibold w-full mb-6">Skill Analysis</h2>
          <div className="w-full h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.1)" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                <Radar name="Candidate" dataKey="A" stroke="#7c3aed" fill="#7c3aed" fillOpacity={0.4} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <div className="w-full mt-6 space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-text-secondary">Recommendation:</span>
              <span className="font-bold text-accent-success uppercase">{report.hiring_recommendation.replace("_", " ")}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-text-secondary">Confidence:</span>
              <span className="font-bold text-text-primary uppercase">{report.hiring_confidence}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-text-secondary">Questions Asked:</span>
              <span className="font-bold text-text-primary">{report.total_questions}</span>
            </div>
          </div>
        </div>

        {/* Middle Column: Strengths & Weaknesses */}
        <div className="glass-panel p-6 space-y-8">
          <div>
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-accent-success">
              <CheckCircle size={20} /> Verified Strengths
            </h2>
            <ul className="space-y-2">
              {report.strong_areas.map((area, i) => (
                <li key={i} className="text-sm bg-accent-success/10 border border-accent-success/20 px-3 py-2 rounded text-text-primary">
                  {area}
                </li>
              ))}
              {report.strong_areas.length === 0 && <li className="text-sm text-text-secondary">Not enough data to confirm strengths.</li>}
            </ul>
          </div>

          <div>
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-accent-danger">
              <XCircle size={20} /> Identified Gaps
            </h2>
            <ul className="space-y-2">
              {report.weak_areas.map((area, i) => (
                <li key={i} className="text-sm bg-accent-danger/10 border border-accent-danger/20 px-3 py-2 rounded text-text-primary">
                  {area}
                </li>
              ))}
              {report.weak_areas.length === 0 && <li className="text-sm text-text-secondary">No significant gaps identified.</li>}
            </ul>
          </div>
          
          <div>
            <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-3">Topics Covered</h2>
            <div className="flex flex-wrap gap-2">
              {report.topics_covered.map((t, i) => (
                <span key={i} className="text-xs px-2 py-1 bg-white/5 rounded border border-white/10">{t}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Learning Roadmap */}
        <div className="glass-panel p-6">
          <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
            <TrendingUp className="text-accent-warning" size={20} /> Personalized Roadmap
          </h2>
          
          <div className="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-white/10 before:to-transparent">
            
            {/* 30 Day */}
            <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
              <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white/20 bg-bg-surface text-accent-primary font-bold shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                30
              </div>
              <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-white/10 bg-white/5">
                <h3 className="font-bold text-text-primary text-sm mb-2">Foundation Repair</h3>
                <ul className="text-xs text-text-secondary space-y-1 list-disc pl-4">
                  {report.learning_plan_30_day.slice(0, 3).map((item, i) => <li key={i}>{item}</li>)}
                </ul>
              </div>
            </div>

            {/* 60 Day */}
            <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
              <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white/20 bg-bg-surface text-accent-secondary font-bold shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                60
              </div>
              <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-white/10 bg-white/5">
                <h3 className="font-bold text-text-primary text-sm mb-2">Applied Skills</h3>
                <ul className="text-xs text-text-secondary space-y-1 list-disc pl-4">
                  {report.learning_plan_60_day.slice(0, 3).map((item, i) => <li key={i}>{item}</li>)}
                </ul>
              </div>
            </div>

            {/* 90 Day */}
            <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
              <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white/20 bg-bg-surface text-accent-success font-bold shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                90
              </div>
              <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-white/10 bg-white/5">
                <h3 className="font-bold text-text-primary text-sm mb-2">Production Scale</h3>
                <ul className="text-xs text-text-secondary space-y-1 list-disc pl-4">
                  {report.learning_plan_90_day.slice(0, 3).map((item, i) => <li key={i}>{item}</li>)}
                </ul>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}
