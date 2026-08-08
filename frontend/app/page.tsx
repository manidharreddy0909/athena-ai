"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { BrainCircuit, Play, ArrowRight, ShieldCheck, ChevronRight, Mic, Code2, Globe2, FileText, LayoutDashboard, Cpu, MessageSquare } from "lucide-react";
import { api, CandidateProfile } from "@/lib/api";

const DOMAINS = [
  { id: "ai_ml", name: "AI / Machine Learning", icon: BrainCircuit },
  { id: "software_engineering", name: "Software Engineering", icon: Code2 },
  { id: "data_engineering", name: "Data Engineering", icon: LayoutDashboard },
  { id: "cloud_devops", name: "Cloud / DevOps", icon: Cpu },
  { id: "custom", name: "Custom Topic", icon: MessageSquare },
];

const MODES = [
  { id: "general", name: "Adaptive General", desc: "Balanced theory & practice" },
  { id: "coding", name: "Deep Coding", desc: "Focus on algorithms & debugging" },
  { id: "system_design", name: "System Design", desc: "Architecture & scalability" },
];

const LANGUAGES = [
  { id: "en", name: "English" },
  { id: "te", name: "Telugu" },
  { id: "es", name: "Español" },
  { id: "hi", name: "Hindi" },
  { id: "fr", name: "Français" },
  { id: "zh", name: "Chinese" },
];

const DIFFICULTIES = [
  { id: "easy", name: "Beginner" },
  { id: "medium", name: "Intermediate" },
  { id: "hard", name: "Advanced" },
  { id: "expert", name: "Expert" },
  { id: "adaptive", name: "Adaptive" }
];

const PERSONALITIES = [
  { id: "professional", name: "Professional" },
  { id: "friendly", name: "Friendly" },
  { id: "strict", name: "Strict" },
  { id: "socratic", name: "Socratic" },
  { id: "faang", name: "FAANG-style" }
];

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [profile, setProfile] = useState<CandidateProfile>({
    name: "Aryan Shah",
    completed_missions: [1, 2, 3, 5, 7],
    skipped_topics: [],
    domain: "ai_ml",
    custom_domain_topic: "",
    mode: "general",
    difficulty: "medium",
    personality: "professional",
    language: "en",
    provider: "gemini",
    resume_text: "",
    jd_text: "",
  });

  const handleStart = async () => {
    setLoading(true);
    try {
      const res = await api.startInterview(profile);
      localStorage.setItem("athena_session_id", res.session_id);
      localStorage.setItem("athena_session_data", JSON.stringify(res));
      router.push("/interview");
    } catch (err) {
      console.error(err);
      alert("Failed to start interview. Check backend connection.");
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4 relative overflow-hidden bg-bg-main text-text-primary">
      {/* Cinematic Background Effects */}
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-accent-primary/10 blur-[150px] rounded-full pointer-events-none animate-pulse-slow" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-accent-secondary/10 blur-[150px] rounded-full pointer-events-none" />
      <div className="absolute inset-0 bg-[url('/noise.png')] opacity-[0.03] pointer-events-none mix-blend-overlay" />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="w-full max-w-5xl z-10 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center"
      >
        {/* Left: Hero Copy */}
        <div className="text-left space-y-6">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-accent-primary mb-4"
          >
            <Activity className="w-4 h-4" /> v2.0 Production Ready
          </motion.div>
          <h1 className="text-6xl md:text-7xl font-bold tracking-tight font-display text-transparent bg-clip-text bg-gradient-to-br from-white to-white/60">
            Athena <br/> Intelligence.
          </h1>
          <p className="text-xl text-text-secondary font-light leading-relaxed max-w-lg">
            The autonomous AI interview operating system. Powered by multi-agent debate, dynamic knowledge graphs, and Socratic evaluation.
          </p>

          <div className="flex gap-4 pt-4">
            <div className="flex items-center gap-2 text-sm text-text-secondary"><Globe2 className="w-4 h-4 text-accent-secondary" /> Multilingual</div>
            <div className="flex items-center gap-2 text-sm text-text-secondary"><Mic className="w-4 h-4 text-accent-primary" /> Voice Enabled</div>
            <div className="flex items-center gap-2 text-sm text-text-secondary"><FileText className="w-4 h-4 text-accent-success" /> Resume Parsing</div>
          </div>
        </div>

        {/* Right: Onboarding Panel */}
        <div className="glass-panel p-8 md:p-10 w-full relative overflow-hidden shadow-2xl shadow-black/50 border border-white/10 rounded-2xl bg-bg-surface/80 backdrop-blur-xl">
          
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-8">
                <div>
                  <h3 className="text-2xl font-semibold mb-2">Candidate Setup</h3>
                  <p className="text-sm text-text-secondary">Configure the digital twin and domain constraints.</p>
                </div>
                
                <div>
                  <label className="block text-sm text-text-secondary mb-2">Candidate Name</label>
                  <input
                    type="text"
                    value={profile.name}
                    onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-3 text-text-primary focus:outline-none focus:border-accent-primary transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-sm text-text-secondary mb-3">Interview Domain</label>
                  <div className="grid grid-cols-2 gap-3">
                    {DOMAINS.map(d => (
                      <button
                        key={d.id}
                        onClick={() => setProfile({ ...profile, domain: d.id })}
                        className={`flex items-center gap-2 p-3 rounded-lg border text-sm transition-all text-left ${profile.domain === d.id ? 'bg-accent-primary/20 border-accent-primary text-accent-primary' : 'bg-black/20 border-white/5 hover:border-white/20 text-text-secondary'}`}
                      >
                        <d.icon className="w-4 h-4" /> {d.name}
                      </button>
                    ))}
                  </div>
                  {profile.domain === "custom" && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="mt-3">
                      <input
                        type="text"
                        placeholder="e.g. Quantum Computing, Kubernetes..."
                        value={profile.custom_domain_topic}
                        onChange={(e) => setProfile({ ...profile, custom_domain_topic: e.target.value })}
                        className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-3 text-text-primary focus:outline-none focus:border-accent-primary transition-colors text-sm"
                      />
                    </motion.div>
                  )}
                </div>

                <div className="flex justify-end pt-4">
                  <button onClick={() => setStep(2)} className="bg-white/10 hover:bg-white/20 text-white font-medium py-2.5 px-6 rounded-lg flex items-center gap-2 transition-all">
                    Next Step <ChevronRight size={18} />
                  </button>
                </div>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-8">
                <div>
                  <h3 className="text-2xl font-semibold mb-2">Interview Engine</h3>
                  <p className="text-sm text-text-secondary">Select evaluation mode and language.</p>
                </div>

                <div>
                  <label className="block text-sm text-text-secondary mb-3">Evaluation Mode</label>
                  <div className="space-y-3">
                    {MODES.map(m => (
                      <button
                        key={m.id}
                        onClick={() => setProfile({ ...profile, mode: m.id })}
                        className={`w-full flex flex-col p-3 rounded-lg border text-left transition-all ${profile.mode === m.id ? 'bg-accent-secondary/20 border-accent-secondary' : 'bg-black/20 border-white/5 hover:border-white/20'}`}
                      >
                        <span className={`text-sm font-medium ${profile.mode === m.id ? 'text-accent-secondary' : 'text-text-primary'}`}>{m.name}</span>
                        <span className="text-xs text-text-secondary mt-1">{m.desc}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm text-text-secondary mb-3">Difficulty</label>
                    <div className="space-y-2">
                      {DIFFICULTIES.map(d => (
                        <button
                          key={d.id}
                          onClick={() => setProfile({ ...profile, difficulty: d.id })}
                          className={`w-full px-3 py-2 text-left rounded-lg border text-sm transition-all ${profile.difficulty === d.id ? 'bg-white/10 text-white border-white/20' : 'bg-transparent border-transparent hover:bg-white/5 text-text-secondary'}`}
                        >
                          {d.name}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm text-text-secondary mb-3">Interviewer Persona</label>
                    <div className="space-y-2">
                      {PERSONALITIES.map(p => (
                        <button
                          key={p.id}
                          onClick={() => setProfile({ ...profile, personality: p.id })}
                          className={`w-full px-3 py-2 text-left rounded-lg border text-sm transition-all ${profile.personality === p.id ? 'bg-white/10 text-white border-white/20' : 'bg-transparent border-transparent hover:bg-white/5 text-text-secondary'}`}
                        >
                          {p.name}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-text-secondary mb-3">Spoken Language</label>
                  <div className="flex flex-wrap gap-2">
                    {LANGUAGES.map(l => (
                      <button
                        key={l.id}
                        onClick={() => setProfile({ ...profile, language: l.id })}
                        className={`px-4 py-2 rounded-full border text-sm transition-all ${profile.language === l.id ? 'bg-white text-black border-white' : 'bg-black/20 border-white/10 hover:border-white/30 text-text-secondary'}`}
                      >
                        {l.name}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex justify-between pt-4">
                  <button onClick={() => setStep(1)} className="text-text-secondary hover:text-white font-medium py-2.5 px-4 transition-all">
                    Back
                  </button>
                  <button onClick={() => setStep(3)} className="bg-white/10 hover:bg-white/20 text-white font-medium py-2.5 px-6 rounded-lg flex items-center gap-2 transition-all">
                    Next Step <ChevronRight size={18} />
                  </button>
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div key="step3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-8">
                <div>
                  <h3 className="text-2xl font-semibold mb-2">Resume Intelligence</h3>
                  <p className="text-sm text-text-secondary">Paste candidate resume for adaptive questioning.</p>
                </div>

                <div>
                  <label className="block text-sm text-text-secondary mb-2 flex justify-between">
                    Resume Text <span className="text-xs opacity-50">(Optional)</span>
                  </label>
                  <textarea
                    value={profile.resume_text}
                    onChange={(e) => setProfile({ ...profile, resume_text: e.target.value })}
                    placeholder="Paste resume here to automatically tailor the interview..."
                    className="w-full h-32 bg-black/40 border border-white/10 rounded-lg px-4 py-3 text-text-primary text-sm focus:outline-none focus:border-accent-primary transition-colors resize-none scrollbar-thin"
                  />
                </div>

                <div className="flex justify-between pt-4">
                  <button onClick={() => setStep(2)} className="text-text-secondary hover:text-white font-medium py-2.5 px-4 transition-all">
                    Back
                  </button>
                  <button
                    onClick={handleStart}
                    disabled={loading}
                    className="bg-gradient-to-r from-accent-primary to-accent-secondary hover:opacity-90 text-white font-semibold py-2.5 px-8 rounded-lg flex items-center gap-2 transition-all disabled:opacity-50"
                  >
                    {loading ? (
                      <span className="flex items-center gap-2 animate-pulse"><Activity size={18} /> Initializing...</span>
                    ) : (
                      <>Launch Interview <Play size={16} fill="currentColor" /></>
                    )}
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

        </div>
      </motion.div>
    </main>
  );
}

// Activity icon for v2 badge
function Activity(props: any) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
  )
}
