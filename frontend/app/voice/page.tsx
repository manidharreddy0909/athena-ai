"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic, MicOff, Square, Loader2, Volume2, VolumeX,
  ArrowLeft, RotateCcw, MessageSquare, CheckCircle, AlertCircle,
  ChevronRight, User, Bot, PauseCircle, PlayCircle, Download
} from "lucide-react";
import { api, StartResponse, RespondResponse } from "@/lib/api";

// ─── 7 Interview States ───────────────────────────────────────────────────────
type InterviewState =
  | "IDLE"         // 1. Ready, waiting for user to begin
  | "AI_THINKING"  // 2. AI is generating/processing
  | "AI_SPEAKING"  // 3. AI is outputting TTS audio
  | "USER_READY"   // 4. AI done speaking, user about to speak
  | "USER_SPEAKING"// 5. User is recording audio
  | "PROCESSING"   // 6. STT + backend evaluation in progress
  | "COMPLETED";   // 7. Interview finished

interface TranscriptEntry {
  role: "ai" | "user";
  text: string;
  topic?: string;
}

// ─── Waveform Visualizer ─────────────────────────────────────────────────────
function WaveformBars({ active, color }: { active: boolean; color: string }) {
  const bars = Array.from({ length: 12 });
  return (
    <div className="flex items-center gap-[3px] h-12">
      {bars.map((_, i) => (
        <motion.div
          key={i}
          className={`w-1 rounded-full ${color}`}
          animate={
            active
              ? { height: [8, Math.random() * 36 + 8, 8] }
              : { height: 6 }
          }
          transition={
            active
              ? { duration: 0.4 + Math.random() * 0.4, repeat: Infinity, delay: i * 0.06 }
              : { duration: 0.2 }
          }
        />
      ))}
    </div>
  );
}

// ─── AI Orb ─────────────────────────────────────────────────────────────────
function AIOrb({ state }: { state: InterviewState }) {
  const isActive = state === "AI_SPEAKING" || state === "AI_THINKING";
  const isPulsing = state === "AI_SPEAKING";
  const isUserSpeaking = state === "USER_SPEAKING" || state === "USER_READY";

  return (
    <div className="relative flex items-center justify-center w-48 h-48">
      {/* Outer glow rings */}
      <AnimatePresence>
        {isPulsing && (
          <>
            <motion.div
              key="ring1"
              className="absolute inset-0 rounded-full border border-indigo-400/30"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1.5, opacity: 0 }}
              transition={{ duration: 2, repeat: Infinity }}
            />
            <motion.div
              key="ring2"
              className="absolute inset-0 rounded-full border border-violet-400/20"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1.8, opacity: 0 }}
              transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
            />
          </>
        )}
        {state === "USER_SPEAKING" && (
          <>
            <motion.div
              key="ring-user1"
              className="absolute inset-0 rounded-full border border-emerald-400/30"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1.5, opacity: 0 }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
            <motion.div
              key="ring-user2"
              className="absolute inset-0 rounded-full border border-emerald-300/20"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1.9, opacity: 0 }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
            />
          </>
        )}
      </AnimatePresence>

      {/* Core orb */}
      <motion.div
        className="w-40 h-40 rounded-full relative overflow-hidden flex items-center justify-center shadow-2xl"
        style={{
          background: state === "USER_SPEAKING" || state === "USER_READY"
            ? "radial-gradient(circle at 35% 35%, #059669, #0d1117 80%)"
            : state === "AI_SPEAKING" || state === "AI_THINKING"
            ? "radial-gradient(circle at 35% 35%, #6366f1, #0d1117 80%)"
            : "radial-gradient(circle at 35% 35%, #374151, #0d1117 80%)",
          border: "1px solid rgba(255,255,255,0.1)",
        }}
        animate={{
          scale: state === "AI_SPEAKING" ? [1, 1.04, 1] : state === "USER_SPEAKING" ? [1, 1.06, 1] : 1,
        }}
        transition={{ duration: state === "AI_SPEAKING" ? 1.8 : 1.2, repeat: Infinity, ease: "easeInOut" }}
      >
        {/* Inner shine */}
        <div className="absolute top-3 left-5 w-8 h-8 bg-white/10 rounded-full blur-sm" />

        {/* State icon */}
        <div className="relative z-10">
          {state === "AI_THINKING" && <Loader2 className="w-10 h-10 text-indigo-300 animate-spin" />}
          {state === "AI_SPEAKING" && <WaveformBars active={true} color="bg-indigo-300" />}
          {state === "USER_SPEAKING" && <WaveformBars active={true} color="bg-emerald-400" />}
          {state === "USER_READY" && <Mic className="w-10 h-10 text-white/60 animate-pulse" />}
          {state === "PROCESSING" && <Loader2 className="w-10 h-10 text-amber-300 animate-spin" />}
          {state === "IDLE" && <Bot className="w-10 h-10 text-white/40" />}
          {state === "COMPLETED" && <CheckCircle className="w-10 h-10 text-emerald-400" />}
        </div>
      </motion.div>
    </div>
  );
}

// ─── State Label ─────────────────────────────────────────────────────────────
function StateLabel({ state, errorMsg }: { state: InterviewState; errorMsg?: string }) {
  const labels: Record<InterviewState, { text: string; color: string }> = {
    IDLE: { text: "Ready — click below to start", color: "text-white/40" },
    AI_THINKING: { text: "Athena is thinking...", color: "text-indigo-300" },
    AI_SPEAKING: { text: "Athena is speaking", color: "text-indigo-400 animate-pulse" },
    USER_READY: { text: "Your turn — tap mic to speak", color: "text-emerald-300" },
    USER_SPEAKING: { text: "Listening...", color: "text-emerald-400 animate-pulse" },
    PROCESSING: { text: "Processing your answer...", color: "text-amber-300" },
    COMPLETED: { text: "Interview complete!", color: "text-emerald-400" },
  };
  const { text, color } = labels[state];
  return (
    <p className={`text-sm font-mono tracking-widest uppercase ${color}`}>
      {errorMsg || text}
    </p>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function VoiceInterviewPage() {
  const router = useRouter();
  const [session, setSession] = useState<StartResponse | null>(null);
  const [interviewState, setInterviewState] = useState<InterviewState>("IDLE");
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<string>("");
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [isMuted, setIsMuted] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [questionNumber, setQuestionNumber] = useState(1);
  const [totalQuestions, setTotalQuestions] = useState(10);
  const [showTextFallback, setShowTextFallback] = useState(false);
  const [textFallbackInput, setTextFallbackInput] = useState("");
  const [lastAnswerScore, setLastAnswerScore] = useState<number | null>(null);
  const [language, setLanguage] = useState("en");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const transcriptEndRef = useRef<HTMLDivElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const sessionIdRef = useRef<string>("");

  const scrollToBottom = () => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // ─── Export Transcript ─────────────────────────────────────────────────────
  const downloadTranscript = () => {
    const text = transcript
      .map((entry) => `[${entry.role.toUpperCase()}] ${entry.text}`)
      .join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `athena_transcript_${sessionIdRef.current || "session"}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // ─── Speak text via TTS ────────────────────────────────────────────────────
  const speakText = useCallback(async (text: string) => {
    if (isMuted) {
      setInterviewState("USER_READY");
      return;
    }
    setInterviewState("AI_THINKING");
    try {
      const blob = await api.textToSpeech(text);
      const url = URL.createObjectURL(blob);
      setInterviewState("AI_SPEAKING");
      if (audioPlayerRef.current) {
        audioPlayerRef.current.src = url;
        audioPlayerRef.current.onended = () => {
          URL.revokeObjectURL(url);
          setInterviewState("USER_READY");
        };
        audioPlayerRef.current.onerror = () => {
          URL.revokeObjectURL(url);
          setInterviewState("USER_READY");
        };
        await audioPlayerRef.current.play();
      }
    } catch (err) {
      console.error("TTS Error:", err);
      // Graceful fallback: skip TTS, go straight to user's turn
      setInterviewState("USER_READY");
    }
  }, [isMuted]);

  // ─── Initialize session ────────────────────────────────────────────────────
  useEffect(() => {
    const sessionId = localStorage.getItem("athena_session_id");
    const storedSession = localStorage.getItem("athena_session_data");
    const storedProfile = localStorage.getItem("athena_profile");

    if (!sessionId || !storedSession) {
      router.push("/");
      return;
    }

    try {
      const parsed: StartResponse = JSON.parse(storedSession);
      sessionIdRef.current = parsed.session_id;
      setSession(parsed);
      setCurrentQuestion(parsed.question);
      setQuestionNumber(parsed.question_number);
      setTotalQuestions(parsed.total_questions_planned);
      setTranscript([{ role: "ai", text: parsed.question, topic: parsed.topic }]);

      if (storedProfile) {
        const profile = JSON.parse(storedProfile);
        setLanguage(profile.language || "en");
      }

      // Speak first question
      speakText(parsed.question);
    } catch {
      router.push("/");
    }
  }, [router, speakText]);

  useEffect(() => {
    scrollToBottom();
  }, [transcript]);

  // ─── Interrupt AI speaking ─────────────────────────────────────────────────
  const interruptAI = () => {
    if (audioPlayerRef.current && !audioPlayerRef.current.paused) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current.currentTime = 0;
    }
    setInterviewState("USER_READY");
  };

  // ─── Toggle mute ──────────────────────────────────────────────────────────
  const toggleMute = () => {
    const newMuted = !isMuted;
    setIsMuted(newMuted);
    if (newMuted && audioPlayerRef.current) {
      audioPlayerRef.current.muted = true;
    } else if (audioPlayerRef.current) {
      audioPlayerRef.current.muted = false;
    }
  };

  // ─── Pause / Resume ───────────────────────────────────────────────────────
  const togglePause = () => {
    if (isPaused) {
      setIsPaused(false);
      if (interviewState === "AI_SPEAKING" && audioPlayerRef.current) {
        audioPlayerRef.current.play();
      }
    } else {
      setIsPaused(true);
      if (audioPlayerRef.current) audioPlayerRef.current.pause();
    }
  };

  // ─── Start recording ──────────────────────────────────────────────────────
  const startRecording = async () => {
    if (interviewState === "AI_SPEAKING") interruptAI();
    setErrorMsg("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Pick best supported MIME
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "audio/ogg;codecs=opus";

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(audioChunksRef.current, { type: mimeType });
        await processAnswer(blob);
      };

      mediaRecorder.start(100);
      setInterviewState("USER_SPEAKING");
    } catch (err: any) {
      const msg = err?.name === "NotAllowedError"
        ? "Microphone access denied. Please allow microphone access and try again."
        : "Microphone unavailable. Try text mode instead.";
      setErrorMsg(msg);
      setShowTextFallback(true);
    }
  };

  // ─── Stop recording ───────────────────────────────────────────────────────
  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    setInterviewState("PROCESSING");
  };

  // ─── Retry ────────────────────────────────────────────────────────────────
  const handleRetry = () => {
    setErrorMsg("");
    setInterviewState("USER_READY");
    // Re-speak the current question
    speakText(currentQuestion);
  };

  // ─── Process the voice answer ─────────────────────────────────────────────
  const processAnswer = async (audioBlob: Blob) => {
    setInterviewState("PROCESSING");
    try {
      // 1. STT
      let recognizedText = "";
      try {
        const sttRes = await api.speechToText(audioBlob);
        recognizedText = sttRes.text;
      } catch (sttErr) {
        throw new Error("Speech-to-text failed. Please try again or use text mode.");
      }

      if (!recognizedText.trim()) {
        setErrorMsg("No speech detected. Please try again.");
        setInterviewState("USER_READY");
        return;
      }

      setTranscript((prev) => [...prev, { role: "user", text: recognizedText }]);

      // 2. Submit answer
      await submitAnswer(recognizedText);
    } catch (err: any) {
      setErrorMsg(err.message || "Something went wrong.");
      setInterviewState("USER_READY");
    }
  };

  // ─── Submit answer (used by both voice and text fallback) ─────────────────
  const submitAnswer = async (answerText: string) => {
    setInterviewState("AI_THINKING");
    try {
      const respondRes = await api.respond(sessionIdRef.current, answerText);
      setLastAnswerScore(respondRes.answer_score ?? null);

      if (respondRes.interview_complete) {
        setInterviewState("COMPLETED");
        setTranscript((prev) => [
          ...prev,
          { role: "ai", text: "Interview complete! Generating your report now..." },
        ]);
        speakText("Thank you. The interview is now complete. Generating your report.");
        setTimeout(() => router.push("/dashboard"), 4000);
      } else {
        const nextQ = respondRes.question!;
        setCurrentQuestion(nextQ);
        setQuestionNumber(respondRes.question_number);
        setTranscript((prev) => [
          ...prev,
          { role: "ai", text: nextQ, topic: respondRes.topic },
        ]);
        speakText(nextQ);
      }
    } catch (err: any) {
      setErrorMsg("Failed to submit answer. Check your connection.");
      setInterviewState("USER_READY");
    }
  };

  // ─── Text fallback submit ─────────────────────────────────────────────────
  const handleTextFallbackSubmit = async () => {
    const text = textFallbackInput.trim();
    if (!text) return;
    setTextFallbackInput("");
    setTranscript((prev) => [...prev, { role: "user", text }]);
    await submitAnswer(text);
  };

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-main">
        <Loader2 className="w-8 h-8 text-accent-primary animate-spin" />
      </div>
    );
  }

  const canSpeak = interviewState === "USER_READY" || interviewState === "AI_SPEAKING";
  const isRecording = interviewState === "USER_SPEAKING";

  return (
    <div className="min-h-screen bg-bg-main text-text-primary flex flex-col relative overflow-hidden">
      {/* Ambient Background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[80vw] h-[50vh] bg-indigo-600/5 blur-[120px] rounded-full" />
        <div className="absolute bottom-0 left-1/4 w-[40vw] h-[30vh] bg-violet-600/5 blur-[100px] rounded-full" />
        <div className="absolute inset-0 bg-[url('/noise.png')] opacity-[0.02] mix-blend-overlay" />
      </div>

      {/* Header */}
      <header className="relative z-10 flex justify-between items-center px-6 py-4 border-b border-white/5">
        <button
          onClick={() => router.push("/interview")}
          className="text-text-secondary hover:text-white flex items-center gap-2 text-sm transition-colors"
        >
          <ArrowLeft size={16} /> Text Mode
        </button>

        <div className="flex items-center gap-4">
          {/* Progress */}
          <div className="flex items-center gap-2">
            <div className="h-1.5 w-32 bg-white/10 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full"
                animate={{ width: `${(questionNumber / (totalQuestions || 10)) * 100}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
            <span className="text-xs font-mono text-text-secondary">
              Q{questionNumber}/{totalQuestions}
            </span>
          </div>

          {/* Language badge */}
          <span className="text-xs px-2 py-1 bg-white/5 border border-white/10 rounded-full font-mono text-text-secondary uppercase">
            {language}
          </span>

          {/* Controls */}
          <button
            onClick={toggleMute}
            title={isMuted ? "Unmute AI" : "Mute AI"}
            className="p-2 rounded-lg border border-white/10 hover:bg-white/5 transition-colors text-text-secondary hover:text-white"
          >
            {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
          </button>
          <button
            onClick={togglePause}
            title={isPaused ? "Resume" : "Pause"}
            className="p-2 rounded-lg border border-white/10 hover:bg-white/5 transition-colors text-text-secondary hover:text-white"
          >
            {isPaused ? <PlayCircle size={16} /> : <PauseCircle size={16} />}
          </button>
          <button
            onClick={() => setShowTextFallback((v) => !v)}
            title="Text fallback mode"
            className={`p-2 rounded-lg border transition-colors ${showTextFallback ? "border-indigo-400 text-indigo-400" : "border-white/10 text-text-secondary hover:text-white hover:bg-white/5"}`}
          >
            <MessageSquare size={16} />
          </button>
        </div>
      </header>

      {/* Main layout */}
      <main className="relative z-10 flex-1 flex gap-0 overflow-hidden">

        {/* Left: Transcript */}
        <div className="w-80 border-r border-white/5 flex flex-col">
          <div className="px-4 py-3 border-b border-white/5 flex justify-between items-center">
            <p className="text-xs font-mono text-text-secondary uppercase tracking-widest">Live Transcript</p>
            {transcript.length > 0 && (
              <button
                onClick={downloadTranscript}
                className="text-text-secondary hover:text-white transition-colors"
                title="Download Transcript"
              >
                <Download size={14} />
              </button>
            )}
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-white/10">
            <AnimatePresence>
              {transcript.map((entry, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-2 ${entry.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                >
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-1 ${entry.role === "ai" ? "bg-indigo-500/20" : "bg-emerald-500/20"}`}>
                    {entry.role === "ai" ? <Bot size={12} className="text-indigo-400" /> : <User size={12} className="text-emerald-400" />}
                  </div>
                  <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed ${entry.role === "ai" ? "bg-white/5 text-white/80" : "bg-emerald-500/10 text-emerald-100 text-right"}`}>
                    {entry.topic && (
                      <p className="text-[10px] font-mono text-text-secondary mb-1 uppercase">{entry.topic}</p>
                    )}
                    {entry.text}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            <div ref={transcriptEndRef} />
          </div>
        </div>

        {/* Center: AI Orb + Controls */}
        <div className="flex-1 flex flex-col items-center justify-center gap-8 px-8">

          {/* Orb */}
          <AIOrb state={interviewState} />

          {/* Current question display */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentQuestion}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="text-center max-w-xl"
            >
              <p className="text-xl font-light text-white/90 leading-relaxed">
                &ldquo;{currentQuestion}&rdquo;
              </p>
            </motion.div>
          </AnimatePresence>

          {/* State label */}
          <StateLabel state={interviewState} errorMsg={errorMsg} />

          {/* Score indicator (after each answer) */}
          <AnimatePresence>
            {lastAnswerScore !== null && interviewState !== "PROCESSING" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="text-xs font-mono text-text-secondary flex items-center gap-2"
              >
                <span>Last answer score:</span>
                <span className={`font-semibold ${lastAnswerScore >= 0.7 ? "text-emerald-400" : lastAnswerScore >= 0.4 ? "text-amber-400" : "text-red-400"}`}>
                  {Math.round(lastAnswerScore * 100)}%
                </span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Main mic button */}
          <div className="flex flex-col items-center gap-4">
            <AnimatePresence mode="wait">
              {interviewState === "COMPLETED" ? (
                <motion.button
                  key="done"
                  onClick={() => router.push("/dashboard")}
                  className="bg-emerald-500 hover:bg-emerald-600 text-white font-semibold px-8 py-3 rounded-full flex items-center gap-2 transition-colors"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  View Report <ChevronRight size={18} />
                </motion.button>
              ) : isRecording ? (
                <motion.button
                  key="stop"
                  onClick={stopRecording}
                  className="w-20 h-20 rounded-full bg-white text-black flex items-center justify-center shadow-2xl hover:scale-105 active:scale-95 transition-transform"
                  initial={{ scale: 0.8 }}
                  animate={{ scale: 1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <Square fill="currentColor" size={24} />
                </motion.button>
              ) : (
                <motion.button
                  key="mic"
                  onClick={canSpeak ? startRecording : undefined}
                  disabled={!canSpeak && interviewState !== "IDLE"}
                  className={`w-20 h-20 rounded-full flex items-center justify-center shadow-xl transition-all
                    ${canSpeak
                      ? "bg-gradient-to-br from-indigo-500 to-violet-600 hover:scale-105 active:scale-95 cursor-pointer"
                      : "bg-white/10 cursor-not-allowed opacity-40"}`}
                  whileTap={canSpeak ? { scale: 0.9 } : undefined}
                >
                  <Mic size={28} className="text-white" />
                </motion.button>
              )}
            </AnimatePresence>

            {/* Secondary controls */}
            <div className="flex items-center gap-3">
              {interviewState === "AI_SPEAKING" && (
                <button
                  onClick={interruptAI}
                  className="text-xs text-text-secondary hover:text-white flex items-center gap-1 transition-colors px-3 py-1.5 rounded-lg border border-white/10 hover:bg-white/5"
                >
                  <Square size={12} /> Interrupt
                </button>
              )}
              {(interviewState === "USER_READY" || errorMsg) && (
                <button
                  onClick={handleRetry}
                  className="text-xs text-text-secondary hover:text-white flex items-center gap-1 transition-colors px-3 py-1.5 rounded-lg border border-white/10 hover:bg-white/5"
                >
                  <RotateCcw size={12} /> Retry Question
                </button>
              )}
              {interviewState === "USER_SPEAKING" && (
                <p className="text-xs text-emerald-400 animate-pulse font-mono">● REC</p>
              )}
            </div>
          </div>

          {/* Error display */}
          <AnimatePresence>
            {errorMsg && (
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-2 text-sm text-red-400 bg-red-400/10 border border-red-400/20 px-4 py-2 rounded-lg max-w-md text-center"
              >
                <AlertCircle size={16} className="flex-shrink-0" />
                {errorMsg}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Text fallback mode */}
          <AnimatePresence>
            {showTextFallback && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="w-full max-w-xl"
              >
                <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3">
                  <p className="text-xs text-text-secondary font-mono uppercase">Text fallback mode</p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={textFallbackInput}
                      onChange={(e) => setTextFallbackInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleTextFallbackSubmit()}
                      placeholder="Type your answer and press Enter..."
                      disabled={interviewState === "PROCESSING" || interviewState === "AI_THINKING"}
                      className="flex-1 bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-indigo-400 transition-colors disabled:opacity-40"
                    />
                    <button
                      onClick={handleTextFallbackSubmit}
                      disabled={!textFallbackInput.trim() || interviewState === "PROCESSING"}
                      className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white text-sm rounded-lg transition-colors disabled:opacity-40 flex items-center gap-1"
                    >
                      Send <ChevronRight size={14} />
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Hidden audio player */}
      <audio ref={audioPlayerRef} className="hidden" />
    </div>
  );
}
