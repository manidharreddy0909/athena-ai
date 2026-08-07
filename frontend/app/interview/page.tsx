"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Cpu, Lightbulb, AlertCircle, Activity } from "lucide-react";
import { api, StartResponse, RespondResponse } from "@/lib/api";

export default function InterviewPage() {
  const router = useRouter();
  const [session, setSession] = useState<StartResponse | null>(null);
  const [status, setStatus] = useState<RespondResponse | null>(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const endOfChatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sessionId = localStorage.getItem("athena_session_id");
    if (!sessionId) {
      router.push("/");
      return;
    }

    // Fetch initial status
    api.getStatus(sessionId)
      .then((data) => {
        if (data.is_complete) {
          router.push("/dashboard");
        } else {
          // Initialize mock session state from status
          setSession({
            session_id: sessionId,
            candidate_id: "cand_abc",
            question_number: data.questions_asked + 1,
            question: "Loading next question...",
            question_type: "theory",
            topic: data.current_topic,
            difficulty_level: 2,
            reasoning_trace: { dependency_path: [], human_explanation: "Continuing interview..." },
            total_questions_planned: 8,
            message: "Resumed",
          });
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error(err);
        router.push("/");
      });
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim() || !session || submitting) return;

    setSubmitting(true);
    try {
      const res = await api.respond(session.session_id, answer);
      setAnswer("");
      if (res.interview_complete) {
        router.push("/dashboard");
      } else {
        setStatus(res);
        setSession((prev) => prev ? { ...prev, ...res, question: res.question! } : null);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to submit answer.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin text-accent-primary"><Activity size={48} /></div>
      </div>
    );
  }

  const currentQ = status ? status.question : session?.question;
  const reasoning = status ? status.reasoning_trace : session?.reasoning_trace;

  return (
    <div className="min-h-screen flex flex-col md:flex-row p-4 md:p-8 gap-6 max-w-7xl mx-auto">
      
      {/* Left Column: Q&A */}
      <div className="flex-1 flex flex-col h-[calc(100vh-4rem)]">
        
        {/* Header */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <Cpu className="text-accent-primary" />
            <h1 className="text-xl font-bold font-display">Athena Interview</h1>
          </div>
          <div className="text-sm font-mono text-text-secondary">
            Question {session?.question_number} / {session?.total_questions_planned}+
          </div>
        </div>

        {/* Chat / Question Area */}
        <div className="flex-1 overflow-y-auto pr-4 space-y-6 scrollbar-thin">
          <AnimatePresence mode="wait">
            <motion.div
              key={session?.question_number}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="bg-bg-surface border border-white/5 rounded-2xl p-6 relative"
            >
              <div className="absolute top-0 left-0 w-1 h-full bg-accent-primary rounded-l-2xl" />
              <div className="flex items-center gap-2 mb-4">
                <span className="px-2 py-1 text-xs font-mono uppercase bg-accent-primary/20 text-accent-primary rounded">
                  {session?.question_type}
                </span>
                <span className="px-2 py-1 text-xs font-mono uppercase bg-white/10 text-text-secondary rounded">
                  Lvl {session?.difficulty_level}
                </span>
                <span className="ml-auto text-sm text-text-secondary">
                  Topic: <span className="text-accent-secondary">{session?.topic}</span>
                </span>
              </div>
              <p className="text-lg leading-relaxed text-text-primary whitespace-pre-wrap font-medium">
                {currentQ}
              </p>
            </motion.div>
          </AnimatePresence>
          <div ref={endOfChatRef} />
        </div>

        {/* Input Area */}
        <div className="mt-6">
          <form onSubmit={handleSubmit} className="relative">
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Type your answer here... (Markdown supported)"
              className="w-full bg-bg-surface border border-white/10 rounded-xl p-4 pr-14 text-text-primary focus:outline-none focus:border-accent-primary transition-colors resize-none min-h-[120px]"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                  handleSubmit(e);
                }
              }}
              disabled={submitting}
            />
            <button
              type="submit"
              disabled={submitting || !answer.trim()}
              className="absolute bottom-4 right-4 p-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary/80 disabled:opacity-50 transition-colors"
            >
              {submitting ? <Activity className="animate-spin" size={20} /> : <Send size={20} />}
            </button>
          </form>
          <div className="text-xs text-text-secondary mt-2 text-right">
            Press Cmd/Ctrl + Enter to submit
          </div>
        </div>
      </div>

      {/* Right Column: Explainable AI & Analytics */}
      <div className="w-full md:w-80 flex flex-col gap-6">
        
        {/* Explainable AI Panel */}
        <div className="glass-panel p-6">
          <h3 className="text-sm font-semibold mb-4 flex items-center gap-2 text-text-primary uppercase tracking-wider">
            <Lightbulb className="text-accent-warning" size={16} /> Why this question?
          </h3>
          <div className="space-y-4">
            <p className="text-sm text-text-secondary leading-relaxed">
              {reasoning?.human_explanation}
            </p>
            {reasoning?.dependency_path && reasoning.dependency_path.length > 0 && (
              <div className="mt-4 pt-4 border-t border-white/10">
                <div className="text-xs text-text-secondary mb-2 uppercase">Knowledge Path</div>
                <div className="flex flex-wrap gap-1">
                  {reasoning.dependency_path.map((node, i) => (
                    <span key={i} className="text-xs font-mono bg-white/5 px-2 py-1 rounded border border-white/10">
                      {node}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Real-time Status */}
        <div className="glass-panel p-6 flex-1">
          <h3 className="text-sm font-semibold mb-4 flex items-center gap-2 text-text-primary uppercase tracking-wider">
            <Activity className="text-accent-success" size={16} /> Interview State
          </h3>
          
          {status?.answer_feedback && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mb-6 p-4 bg-accent-success/10 border border-accent-success/20 rounded-lg"
            >
              <div className="text-xs font-bold text-accent-success mb-1">PREVIOUS ANSWER SCORE: {Math.round(status.answer_score! * 100)}%</div>
              <p className="text-xs text-text-secondary">{status.answer_feedback}</p>
            </motion.div>
          )}

          <div className="space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-text-secondary">AI Agents Active</span>
              <span className="font-mono text-accent-secondary">8/8</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-text-secondary">Difficulty Engine</span>
              <span className="font-mono text-accent-warning">Adaptive</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-text-secondary">Memory Sync</span>
              <span className="font-mono text-accent-success">Real-time</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
