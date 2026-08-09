"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Camera, CameraOff, Send, Cpu, Lightbulb, Activity,
  ChevronDown, ChevronUp, AlertCircle, Eye, Clock
} from "lucide-react";
import { api, StartResponse, RespondResponse } from "@/lib/api";

type VideoInterviewState = "WAITING" | "READING" | "ANSWERING" | "SUBMITTED" | "COMPLETE";

interface QAHistoryItem {
  question: string;
  answer: string;
  topic: string;
  score?: number;
  feedback?: string;
  question_number: number;
}

function useCamera() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraActive(true);
      setCameraError(null);
    } catch (err: any) {
      setCameraError(
        err.name === "NotAllowedError"
          ? "Camera permission denied. Please allow camera access."
          : "Could not access camera. Check your device settings."
      );
    }
  }, []);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setCameraActive(false);
  }, []);

  useEffect(() => () => { stopCamera(); }, [stopCamera]);

  return { videoRef, cameraActive, cameraError, startCamera, stopCamera };
}

function ElapsedTimer({ active }: { active: boolean }) {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    if (!active) { setSeconds(0); return; }
    const interval = setInterval(() => setSeconds(s => s + 1), 1000);
    return () => clearInterval(interval);
  }, [active]);
  const m = Math.floor(seconds / 60).toString().padStart(2, "0");
  const s = (seconds % 60).toString().padStart(2, "0");
  return <span className="font-mono text-sm text-accent-warning">{m}:{s}</span>;
}

export default function VideoInterviewPage() {
  const router = useRouter();
  const { videoRef, cameraActive, cameraError, startCamera, stopCamera } = useCamera();
  const [session, setSession] = useState<StartResponse | null>(null);
  const [status, setStatus] = useState<RespondResponse | null>(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [history, setHistory] = useState<QAHistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [interviewState, setInterviewState] = useState<VideoInterviewState>("WAITING");
  const [readingTimer, setReadingTimer] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sessionId = localStorage.getItem("athena_session_id");
    if (!sessionId) { router.push("/"); return; }
    const stored = localStorage.getItem("athena_session_data");
    if (stored) {
      try {
        setSession(JSON.parse(stored));
        setLoading(false);
        setInterviewState("READING");
        return;
      } catch {}
    }
    router.push("/");
  }, [router]);

  useEffect(() => {
    if (interviewState !== "READING") { setReadingTimer(0); return; }
    const interval = setInterval(() => setReadingTimer(t => t + 1), 1000);
    return () => clearInterval(interval);
  }, [interviewState]);

  useEffect(() => {
    if (readingTimer >= 30 && interviewState === "READING") {
      setInterviewState("ANSWERING");
    }
  }, [readingTimer, interviewState]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.question_number]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim() || !session || submitting) return;
    const currentAnswer = answer.trim();
    const currentQuestion = status ? status.question! : session.question;
    const currentTopic = status ? status.topic! : session.topic;
    const currentQNum = session.question_number;

    setSubmitting(true);
    setInterviewState("SUBMITTED");
    setAnswer("");

    try {
      const res = await api.respond(session.session_id, currentAnswer);
      setHistory(prev => [...prev, {
        question: currentQuestion, answer: currentAnswer,
        topic: currentTopic, score: res.answer_score,
        feedback: res.answer_feedback, question_number: currentQNum,
      }]);
      if (res.interview_complete) {
        setInterviewState("COMPLETE");
        localStorage.removeItem("athena_session_data");
        setTimeout(() => router.push("/dashboard"), 2000);
      } else {
        setStatus(res);
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
        setInterviewState("READING");
        setReadingTimer(0);
      }
    } catch {
      setAnswer(currentAnswer);
      setInterviewState("ANSWERING");
      alert("Failed to submit answer. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin text-accent-primary mx-auto w-fit"><Activity size={48} /></div>
          <p className="text-text-secondary animate-pulse">Loading Video Interview...</p>
        </div>
      </div>
    );
  }
  if (!session) return null;

  const currentQ = status?.question ?? session.question;
  const stateColors: Record<VideoInterviewState, string> = {
    WAITING: "border-white/20 text-text-secondary",
    READING: "border-accent-secondary/50 text-accent-secondary",
    ANSWERING: "border-accent-primary/50 text-accent-primary",
    SUBMITTED: "border-accent-success/50 text-accent-success",
    COMPLETE: "border-accent-success text-accent-success",
  };
  const stateLabel: Record<VideoInterviewState, string> = {
    WAITING: "Initializing",
    READING: `Reading (${Math.max(0, 30 - readingTimer)}s)`,
    ANSWERING: "Answering",
    SUBMITTED: "Processing",
    COMPLETE: "Complete",
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row p-4 md:p-6 gap-5 max-w-7xl mx-auto">

      {/* Left: Camera + State */}
      <div className="w-full md:w-80 flex flex-col gap-4 shrink-0">

        {/* Camera Feed */}
        <div className="glass-panel overflow-hidden relative aspect-[4/3] bg-black rounded-2xl">
          {cameraActive ? (
            <video
              ref={videoRef}
              autoPlay
              muted
              playsInline
              className="w-full h-full object-cover scale-x-[-1]"
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center gap-3 text-text-secondary">
              <CameraOff size={40} className="opacity-40" />
              <p className="text-sm opacity-60 text-center px-4">
                {cameraError || "Enable camera for self-monitoring"}
              </p>
            </div>
          )}
          <button
            onClick={cameraActive ? stopCamera : startCamera}
            className={`absolute bottom-3 right-3 p-2.5 rounded-full border backdrop-blur-sm transition-all ${
              cameraActive
                ? "bg-accent-danger/20 border-accent-danger/40 text-accent-danger hover:bg-accent-danger/30"
                : "bg-accent-primary/20 border-accent-primary/40 text-accent-primary hover:bg-accent-primary/30"
            }`}
          >
            {cameraActive ? <CameraOff size={16} /> : <Camera size={16} />}
          </button>
          {cameraActive && (
            <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-sm border border-white/10 text-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-danger animate-pulse" />
              <span className="text-white/80">LIVE PREVIEW</span>
            </div>
          )}
        </div>

        {/* Interview State Panel */}
        <div className={`glass-panel p-4 border transition-colors ${stateColors[interviewState]}`}>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono uppercase tracking-wider text-text-secondary">Status</span>
            <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${stateColors[interviewState]} bg-white/5`}>
              {stateLabel[interviewState]}
            </span>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-text-secondary">Question</span>
              <span className="font-mono text-text-primary">Q{session.question_number}/{session.total_questions_planned}+</span>
            </div>
            <div className="flex justify-between items-start">
              <span className="text-text-secondary">Topic</span>
              <span className="text-accent-secondary text-xs text-right max-w-[130px] leading-snug">{session.topic}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">Difficulty</span>
              <span className="font-mono text-text-primary">Level {session.difficulty_level}</span>
            </div>
            {interviewState === "ANSWERING" && (
              <div className="flex justify-between border-t border-white/10 pt-2 mt-1">
                <span className="text-text-secondary flex items-center gap-1"><Clock size={12} /> Time</span>
                <ElapsedTimer active={interviewState === "ANSWERING"} />
              </div>
            )}
          </div>
          {/* Score mini chart */}
          {history.length > 0 && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <div className="text-xs text-text-secondary mb-2">Answer Scores</div>
              <div className="flex items-end gap-1 h-8">
                {history.map((item, i) => (
                  <div
                    key={i}
                    className={`flex-1 rounded-t transition-all ${(item.score || 0) >= 0.65 ? "bg-accent-success" : "bg-accent-danger"}`}
                    style={{ height: `${Math.round((item.score || 0.5) * 100)}%` }}
                    title={`Q${item.question_number}: ${Math.round((item.score || 0) * 100)}%`}
                  />
                ))}
              </div>
            </div>
          )}
          {/* Progress bar */}
          <div className="mt-4">
            <div className="h-1 bg-white/10 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-accent-primary rounded-full"
                animate={{ width: `${Math.min(100, ((session.question_number - 1) / session.total_questions_planned) * 100)}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>
        </div>

        {/* Explainable AI */}
        <div className="glass-panel p-5">
          <h3 className="text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-2 text-text-secondary">
            <Lightbulb size={13} className="text-accent-warning" /> Why This Question?
          </h3>
          <p className="text-xs text-text-secondary leading-relaxed">
            {session.reasoning_trace?.human_explanation || "Analyzing your knowledge profile…"}
          </p>
          {session.reasoning_trace?.dependency_path && session.reasoning_trace.dependency_path.length > 0 && (
            <div className="mt-3 pt-3 border-t border-white/10">
              <div className="text-xs text-text-secondary mb-1.5">Knowledge Path</div>
              <div className="flex flex-wrap gap-1">
                {session.reasoning_trace.dependency_path.slice(0, 4).map((node, i) => (
                  <span key={i} className="text-xs font-mono bg-white/5 px-1.5 py-0.5 rounded border border-white/10 text-text-secondary">
                    {node}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right: Q&A */}
      <div className="flex-1 flex flex-col min-h-0" style={{ height: "calc(100vh - 5rem)" }}>
        {/* Header */}
        <div className="flex items-center justify-between mb-5 pb-4 border-b border-white/10 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center">
              <Eye className="text-white" size={15} />
            </div>
            <h1 className="text-lg font-bold font-display">Video Interview</h1>
          </div>
          {history.length > 0 && (
            <button
              onClick={() => setShowHistory(h => !h)}
              className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors"
            >
              {showHistory ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              {history.length} answered
            </button>
          )}
        </div>

        {/* History (collapsible) */}
        <AnimatePresence>
          {showHistory && history.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-4 space-y-2 overflow-hidden shrink-0"
            >
              {history.map((item, i) => (
                <div key={i} className="bg-bg-surface border border-white/5 rounded-xl p-3 text-xs">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-text-secondary">Q{item.question_number}</span>
                    <span className="px-1.5 py-0.5 bg-white/5 rounded text-text-secondary">{item.topic}</span>
                    {item.score !== undefined && (
                      <span className={`ml-auto font-mono font-bold ${item.score >= 0.65 ? "text-accent-success" : "text-accent-danger"}`}>
                        {Math.round(item.score * 100)}%
                      </span>
                    )}
                  </div>
                  <p className="text-text-secondary italic truncate">"{item.question}"</p>
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Current Question */}
        <div className="flex-1 overflow-y-auto scrollbar-thin space-y-4 pr-1">
          <AnimatePresence mode="wait">
            <motion.div
              key={session.question_number}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="bg-bg-surface border border-white/8 rounded-2xl p-6 relative"
            >
              <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-accent-primary to-accent-secondary rounded-l-2xl" />
              <div className="flex flex-wrap items-center gap-2 mb-5">
                <span className="px-2 py-0.5 text-xs font-mono uppercase bg-accent-primary/20 text-accent-primary rounded-md">
                  {session.question_type}
                </span>
                <span className="px-2 py-0.5 text-xs font-mono uppercase bg-white/8 text-text-secondary rounded-md">
                  Lvl {session.difficulty_level}
                </span>
                <span className="ml-auto text-xs">
                  Topic: <span className="text-accent-secondary">{session.topic}</span>
                </span>
              </div>
              <p className="text-xl leading-relaxed font-medium whitespace-pre-wrap">
                {currentQ}
              </p>

              {/* Reading countdown bar */}
              {interviewState === "READING" && (
                <div className="mt-5 flex items-center gap-3">
                  <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-accent-secondary rounded-full"
                      initial={{ width: "100%" }}
                      animate={{ width: "0%" }}
                      transition={{ duration: 30, ease: "linear" }}
                    />
                  </div>
                  <span className="text-xs text-accent-secondary font-mono shrink-0">
                    {Math.max(0, 30 - readingTimer)}s to answer
                  </span>
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          {/* Previous answer feedback */}
          <AnimatePresence>
            {status?.answer_feedback && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={`p-4 rounded-xl border text-sm ${
                  (status.answer_score || 0) >= 0.65
                    ? "bg-accent-success/10 border-accent-success/20"
                    : "bg-accent-warning/10 border-accent-warning/20"
                }`}
              >
                <div className={`text-xs font-bold mb-1.5 ${(status.answer_score || 0) >= 0.65 ? "text-accent-success" : "text-accent-warning"}`}>
                  PREVIOUS — {Math.round((status.answer_score || 0) * 100)}%
                </div>
                <p className="text-text-secondary text-sm">{status.answer_feedback}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Complete */}
          <AnimatePresence>
            {interviewState === "COMPLETE" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-10 rounded-2xl bg-accent-success/10 border border-accent-success/30 text-center"
              >
                <div className="text-5xl mb-4">🎯</div>
                <h2 className="text-2xl font-bold text-accent-success mb-2 font-display">Interview Complete!</h2>
                <p className="text-text-secondary">Generating your intelligence report...</p>
              </motion.div>
            )}
          </AnimatePresence>

          <div ref={endRef} />
        </div>

        {/* Answer Input */}
        {interviewState !== "COMPLETE" && (
          <div className="mt-4 shrink-0">
            {interviewState === "READING" && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mb-2.5 text-xs text-accent-secondary flex items-center gap-1.5"
              >
                <Activity size={11} className="animate-pulse" />
                Read the question carefully. Click the field or wait for the timer to start answering.
              </motion.p>
            )}
            <form onSubmit={handleSubmit} className="relative">
              <textarea
                ref={textareaRef}
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                onClick={() => { if (interviewState === "READING") setInterviewState("ANSWERING"); }}
                onFocus={() => { if (interviewState === "READING") setInterviewState("ANSWERING"); }}
                placeholder={
                  interviewState === "READING"
                    ? "Click to start answering (or wait for countdown)..."
                    : "Type your answer... (Ctrl+Enter to submit)"
                }
                className="w-full bg-bg-surface border border-white/10 rounded-2xl p-5 pr-16 text-text-primary focus:outline-none focus:border-accent-primary transition-colors resize-none min-h-[120px] scrollbar-thin text-sm"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit(e);
                }}
                disabled={submitting || interviewState === "SUBMITTED"}
              />
              <button
                type="submit"
                disabled={submitting || !answer.trim() || interviewState === "SUBMITTED"}
                className="absolute bottom-4 right-4 p-3 bg-accent-primary text-white rounded-xl hover:bg-accent-primary/80 disabled:opacity-40 transition-all shadow-lg shadow-accent-primary/20"
              >
                {submitting
                  ? <Activity className="animate-spin" size={18} />
                  : <Send size={18} />
                }
              </button>
            </form>
            <div className="text-xs text-text-secondary mt-2 text-right">Ctrl+Enter to submit</div>
          </div>
        )}
      </div>
    </div>
  );
}
