"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Cpu, Lightbulb, AlertCircle, Activity, ChevronDown, ChevronUp } from "lucide-react";
import { api, StartResponse, RespondResponse } from "@/lib/api";

interface QAHistoryItem {
  question: string;
  answer: string;
  topic: string;
  score?: number;
  feedback?: string;
  question_number: number;
}

export default function InterviewPage() {
  const router = useRouter();
  const [session, setSession] = useState<StartResponse | null>(null);
  const [status, setStatus] = useState<RespondResponse | null>(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [history, setHistory] = useState<QAHistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const endOfChatRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const sessionId = localStorage.getItem("athena_session_id");
    if (!sessionId) {
      router.push("/");
      return;
    }

    // Try to restore full session state from localStorage (set during start)
    const storedSession = localStorage.getItem("athena_session_data");
    if (storedSession) {
      try {
        const parsed: StartResponse = JSON.parse(storedSession);
        setSession(parsed);
        setLoading(false);
        return;
      } catch {
        // Fall through to status fetch
      }
    }

    // Fallback: fetch status (for page refresh cases)
    api.getStatus(sessionId)
      .then((data) => {
        if (data.is_complete) {
          router.push("/dashboard");
        } else {
          // Status doesn't include question text, redirect to start
          router.push("/");
        }
      })
      .catch((err) => {
        console.error(err);
        router.push("/");
      });
  }, [router]);

  // Auto-scroll to bottom when question changes
  useEffect(() => {
    endOfChatRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.question_number]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim() || !session || submitting) return;

    const currentAnswer = answer.trim();
    const currentQuestion = status ? status.question! : session.question;
    const currentTopic = status ? status.topic! : session.topic;
    const currentQNum = session.question_number;

    setSubmitting(true);
    setAnswer("");

    try {
      const res = await api.respond(session.session_id, currentAnswer);

      // Record history
      setHistory(prev => [...prev, {
        question: currentQuestion,
        answer: currentAnswer,
        topic: currentTopic,
        score: res.answer_score,
        feedback: res.answer_feedback,
        question_number: currentQNum,
      }]);

      if (res.interview_complete) {
        localStorage.removeItem("athena_session_data");
        router.push("/dashboard");
      } else {
        setStatus(res);
        // Update session with next question data
        setSession(prev => prev ? {
          ...prev,
          question_number: res.question_number,
          question: res.question!,
          question_type: res.question_type || prev.question_type,
          topic: res.topic || prev.topic,
          curriculum_day: res.curriculum_day,
          difficulty_level: res.difficulty_level || prev.difficulty_level,
          reasoning_trace: res.reasoning_trace || prev.reasoning_trace,
        } : null);
      }
    } catch (err) {
      console.error(err);
      setAnswer(currentAnswer); // restore on error
      alert("Failed to submit answer. Please try again.");
    } finally {
      setSubmitting(false);
      textareaRef.current?.focus();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin text-accent-primary mx-auto w-fit"><Activity size={48} /></div>
          <p className="text-text-secondary animate-pulse">Initializing Athena Interview...</p>
        </div>
      </div>
    );
  }

  if (!session) return null;

  const currentQ = session.question;
  const reasoning = session.reasoning_trace;
  const lastStatus = status;

  return (
    <div className="min-h-screen flex flex-col md:flex-row p-4 md:p-8 gap-6 max-w-7xl mx-auto">
      
      {/* Left Column: Q&A */}
      <div className="flex-1 flex flex-col" style={{ height: "calc(100vh - 4rem)" }}>
        
        {/* Header */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <Cpu className="text-accent-primary" />
            <h1 className="text-xl font-bold font-display">Athena Interview</h1>
          </div>
          <div className="flex items-center gap-4">
            {history.length > 0 && (
              <button
                onClick={() => setShowHistory(h => !h)}
                className="flex items-center gap-1 text-xs text-text-secondary hover:text-text-primary transition-colors"
              >
                {showHistory ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                {history.length} answered
              </button>
            )}
            <div className="text-sm font-mono text-text-secondary">
              Q{session.question_number} / {session.total_questions_planned}+
            </div>
          </div>
        </div>

        {/* Answer History (collapsible) */}
        <AnimatePresence>
          {showHistory && history.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-4 space-y-3 overflow-hidden"
            >
              {history.map((item, i) => (
                <div key={i} className="bg-bg-surface border border-white/5 rounded-xl p-4 text-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs text-text-secondary font-mono">Q{item.question_number}</span>
                    <span className="text-xs px-1.5 py-0.5 bg-white/5 rounded text-text-secondary">{item.topic}</span>
                    {item.score !== undefined && (
                      <span className={`text-xs font-mono ml-auto ${item.score >= 0.65 ? 'text-accent-success' : 'text-accent-danger'}`}>
                        {Math.round(item.score * 100)}%
                      </span>
                    )}
                  </div>
                  <p className="text-text-secondary text-xs mb-1 italic">"{item.question}"</p>
                  <p className="text-text-primary text-xs">{item.answer.slice(0, 150)}{item.answer.length > 150 ? '...' : ''}</p>
                  {item.feedback && (
                    <p className="text-text-secondary text-xs mt-2 border-t border-white/5 pt-2">{item.feedback}</p>
                  )}
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Current Question Area */}
        <div className="flex-1 overflow-y-auto pr-2 space-y-6 scrollbar-thin">
          <AnimatePresence mode="wait">
            <motion.div
              key={session.question_number}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              className="bg-bg-surface border border-white/5 rounded-2xl p-6 relative"
            >
              <div className="absolute top-0 left-0 w-1 h-full bg-accent-primary rounded-l-2xl" />
              <div className="flex items-center gap-2 mb-4">
                <span className="px-2 py-1 text-xs font-mono uppercase bg-accent-primary/20 text-accent-primary rounded">
                  {session.question_type}
                </span>
                <span className="px-2 py-1 text-xs font-mono uppercase bg-white/10 text-text-secondary rounded">
                  Lvl {session.difficulty_level}
                </span>
                <span className="ml-auto text-sm text-text-secondary">
                  Topic: <span className="text-accent-secondary">{session.topic}</span>
                </span>
              </div>
              <p className="text-lg leading-relaxed text-text-primary whitespace-pre-wrap font-medium">
                {currentQ}
              </p>
            </motion.div>
          </AnimatePresence>

          {/* Last answer feedback */}
          <AnimatePresence>
            {lastStatus?.answer_feedback && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={`p-4 rounded-xl border text-sm ${
                  (lastStatus.answer_score || 0) >= 0.65
                    ? 'bg-accent-success/10 border-accent-success/20'
                    : 'bg-accent-warning/10 border-accent-warning/20'
                }`}
              >
                <div className={`text-xs font-bold mb-1 ${(lastStatus.answer_score || 0) >= 0.65 ? 'text-accent-success' : 'text-accent-warning'}`}>
                  PREVIOUS ANSWER — {Math.round((lastStatus.answer_score || 0) * 100)}%
                </div>
                <p className="text-text-secondary">{lastStatus.answer_feedback}</p>
              </motion.div>
            )}
          </AnimatePresence>

          <div ref={endOfChatRef} />
        </div>

        {/* Input Area */}
        <div className="mt-6">
          <form onSubmit={handleSubmit} className="relative">
            <textarea
              ref={textareaRef}
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
              className="absolute bottom-4 right-4 p-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary/80 disabled:opacity-50 transition-all"
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
              {reasoning?.human_explanation || "Analyzing your knowledge profile..."}
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
          
          <div className="space-y-4">
            {/* Progress */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-text-secondary">Progress</span>
                <span className="text-text-primary font-mono">{session.question_number - 1} / {session.total_questions_planned}</span>
              </div>
              <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-accent-primary rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(100, ((session.question_number - 1) / session.total_questions_planned) * 100)}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            </div>

            {/* Score history mini chart */}
            {history.length > 0 && (
              <div>
                <div className="text-xs text-text-secondary mb-2 uppercase">Answer Scores</div>
                <div className="flex items-end gap-1 h-12">
                  {history.map((item, i) => (
                    <div
                      key={i}
                      className={`flex-1 rounded-t transition-all ${
                        (item.score || 0) >= 0.65 ? 'bg-accent-success' : 'bg-accent-danger'
                      }`}
                      style={{ height: `${Math.round((item.score || 0.5) * 100)}%` }}
                      title={`Q${item.question_number}: ${Math.round((item.score || 0) * 100)}%`}
                    />
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-3 pt-2 border-t border-white/10">
              <div className="flex justify-between items-center text-sm">
                <span className="text-text-secondary">Difficulty Engine</span>
                <span className="font-mono text-accent-warning">Adaptive</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-text-secondary">Memory Sync</span>
                <span className="font-mono text-accent-success">Real-time</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-text-secondary">Current Day</span>
                <span className="font-mono text-accent-secondary">
                  {session.curriculum_day ? `Day ${session.curriculum_day}` : "N/A"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
