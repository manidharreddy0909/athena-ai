"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Square, Loader2, Volume2, ArrowLeft } from "lucide-react";
import { api, StartResponse, RespondResponse } from "@/lib/api";

export default function VoiceInterviewPage() {
  const router = useRouter();
  const [session, setSession] = useState<StartResponse | null>(null);
  const [status, setStatus] = useState<RespondResponse | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState<string>("");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  const speakText = useCallback(async (text: string) => {
    setIsProcessing(true);
    try {
      const blob = await api.textToSpeech(text);
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
      setIsSpeaking(true);
      
      if (audioPlayerRef.current) {
        audioPlayerRef.current.src = url;
        audioPlayerRef.current.play();
      }
    } catch (err) {
      console.error("TTS Error:", err);
    } finally {
      setIsProcessing(false);
    }
  }, []);

  // Initialize session
  useEffect(() => {
    const sessionId = localStorage.getItem("athena_session_id");
    if (!sessionId) {
      router.push("/");
      return;
    }

    const storedSession = localStorage.getItem("athena_session_data");
    if (storedSession) {
      try {
        const parsed: StartResponse = JSON.parse(storedSession);
        setSession(parsed);
        // Automatically speak the first question
        speakText(parsed.question);
      } catch (err) {
        console.error("Failed to parse session", err);
        router.push("/");
      }
    } else {
      router.push("/");
    }
    
    // Cleanup audio URL on unmount
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [router, audioUrl, speakText]);

  const handleAudioEnd = () => {
    setIsSpeaking(false);
  };

  const toggleRecording = async () => {
    if (isRecording) {
      // Stop recording
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    } else {
      // Start recording
      try {
        if (isSpeaking && audioPlayerRef.current) {
          audioPlayerRef.current.pause();
          setIsSpeaking(false);
        }
        
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) audioChunksRef.current.push(event.data);
        };

        mediaRecorder.onstop = async () => {
          stream.getTracks().forEach(track => track.stop());
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          await processVoiceInput(audioBlob);
        };

        mediaRecorder.start();
        setIsRecording(true);
      } catch (err) {
        console.error("Microphone error:", err);
        alert("Microphone access denied or unavailable.");
      }
    }
  };

  const processVoiceInput = async (audioBlob: Blob) => {
    setIsProcessing(true);
    setTranscript("Transcribing audio...");
    try {
      // 1. Speech to Text
      const sttRes = await api.speechToText(audioBlob);
      const recognizedText = sttRes.text;
      setTranscript(`You: "${recognizedText}"`);
      
      // 2. Submit Answer to Backend
      if (session) {
        const respondRes = await api.respond(session.session_id, recognizedText);
        
        if (respondRes.interview_complete) {
          speakText("Interview complete. Generating report now.");
          setTimeout(() => router.push("/dashboard"), 3000);
        } else {
          setStatus(respondRes);
          setSession(prev => prev ? {
            ...prev,
            question_number: respondRes.question_number,
            question: respondRes.question!,
            topic: respondRes.topic || prev.topic,
          } : null);
          
          // 3. Speak next question
          await speakText(respondRes.question!);
        }
      }
    } catch (err) {
      console.error(err);
      setTranscript("Error processing voice input. Try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  if (!session) return null;

  return (
    <div className="min-h-screen bg-bg-main text-text-primary flex flex-col relative overflow-hidden">
      {/* Background Ambience */}
      <div className="absolute inset-0 bg-[url('/noise.png')] opacity-[0.03] pointer-events-none mix-blend-overlay" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80vh] h-[80vh] bg-accent-primary/5 blur-[120px] rounded-full pointer-events-none" />

      {/* Header */}
      <header className="p-6 flex justify-between items-center z-10">
        <button onClick={() => router.push("/interview")} className="text-text-secondary hover:text-white flex items-center gap-2 text-sm transition-colors">
          <ArrowLeft size={16} /> Text Mode
        </button>
        <div className="font-mono text-xs text-text-secondary">
          Q{session.question_number} / {session.total_questions_planned}+
        </div>
      </header>

      {/* Main UI */}
      <main className="flex-1 flex flex-col items-center justify-center p-6 z-10">
        
        {/* Voice Orb */}
        <div className="relative mb-16">
          <AnimatePresence>
            {(isSpeaking || isProcessing) && (
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.8, 0.5] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                className="absolute inset-0 bg-accent-primary/30 rounded-full blur-2xl"
              />
            )}
            {isRecording && (
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: [1, 1.4, 1], opacity: [0.3, 0.6, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                className="absolute inset-0 bg-accent-danger/30 rounded-full blur-2xl"
              />
            )}
          </AnimatePresence>

          <motion.div
            animate={{
              scale: isRecording ? 1.05 : isSpeaking ? [1, 1.05, 1] : 1,
            }}
            transition={{ duration: isSpeaking ? 2 : 0.3, repeat: isSpeaking ? Infinity : 0 }}
            className={`w-48 h-48 rounded-full flex items-center justify-center border border-white/10 shadow-2xl relative z-10 transition-colors duration-500
              ${isRecording ? 'bg-gradient-to-br from-accent-danger/20 to-black' 
              : isSpeaking ? 'bg-gradient-to-br from-accent-primary/30 to-accent-secondary/10' 
              : 'bg-black/50'} backdrop-blur-xl`}
          >
            {isProcessing ? (
              <Loader2 className="w-12 h-12 text-accent-primary animate-spin" />
            ) : isRecording ? (
              <Mic className="w-12 h-12 text-accent-danger" />
            ) : (
              <Volume2 className="w-12 h-12 text-white/50" />
            )}
          </motion.div>
        </div>

        {/* Current State Text */}
        <div className="text-center max-w-2xl space-y-6">
          <motion.div
            key={session.question}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-2xl font-light leading-relaxed text-white/90"
          >
            &quot;{status?.question || session.question}&quot;
          </motion.div>

          {transcript && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-sm text-text-secondary font-mono bg-white/5 px-4 py-2 rounded-lg inline-block"
            >
              {transcript}
            </motion.div>
          )}
        </div>

        {/* Controls */}
        <div className="mt-16">
          <button
            onClick={toggleRecording}
            disabled={isProcessing}
            className={`w-20 h-20 rounded-full flex items-center justify-center transition-all shadow-xl hover:scale-105 active:scale-95 disabled:opacity-50 disabled:hover:scale-100
              ${isRecording ? 'bg-white text-black' : 'bg-accent-primary text-white'}`}
          >
            {isRecording ? <Square fill="currentColor" size={24} /> : <Mic size={28} />}
          </button>
        </div>
        <div className="mt-4 text-xs text-text-secondary tracking-widest uppercase">
          {isRecording ? 'Tap to Stop' : 'Tap to Speak'}
        </div>

      </main>

      {/* Hidden Audio Player */}
      <audio ref={audioPlayerRef} onEnded={handleAudioEnd} className="hidden" />
    </div>
  );
}
