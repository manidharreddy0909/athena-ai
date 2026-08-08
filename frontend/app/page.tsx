"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { BrainCircuit, Play, ArrowRight, ShieldCheck } from "lucide-react";
import { api, CandidateProfile } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<CandidateProfile>({
    name: "Aryan Shah",
    completed_missions: [1, 2, 3, 5, 7],
    skipped_topics: ["Quantization"],
  });

  const handleStart = async () => {
    setLoading(true);
    try {
      const res = await api.startInterview(profile);
      // Store session ID and full session data (including first question) for interview page
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
    <main className="min-h-screen flex flex-col items-center justify-center p-8 relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-accent-primary/20 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-accent-secondary/20 blur-[120px] rounded-full pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-4xl z-10"
      >
        <div className="text-center mb-12">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="flex items-center justify-center gap-3 mb-6 text-accent-primary"
          >
            <BrainCircuit size={48} strokeWidth={1.5} />
            <h1 className="text-5xl font-bold tracking-tight text-text-primary">Athena AI</h1>
          </motion.div>
          <p className="text-xl text-text-secondary max-w-2xl mx-auto font-light leading-relaxed">
            Autonomous Interview Intelligence Platform. <br/>
            Adaptive questioning powered by multi-agent debate and candidate digital twins.
          </p>
        </div>

        <div className="glass-panel p-8 md:p-12 w-full">
          <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
            <ShieldCheck className="text-accent-secondary" /> Candidate Profile
          </h2>
          
          <div className="space-y-6">
            <div>
              <label className="block text-sm text-text-secondary mb-2">Full Name</label>
              <input
                type="text"
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                className="w-full bg-bg-surface border border-white/10 rounded-lg px-4 py-3 text-text-primary focus:outline-none focus:border-accent-primary transition-colors"
                placeholder="Enter candidate name..."
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm text-text-secondary mb-2">Completed Days (comma-separated)</label>
                <input
                  type="text"
                  value={profile.completed_missions.join(", ")}
                  onChange={(e) => {
                    const days = e.target.value.split(",").map(s => parseInt(s.trim())).filter(n => !isNaN(n));
                    setProfile({ ...profile, completed_missions: days });
                  }}
                  className="w-full bg-bg-surface border border-white/10 rounded-lg px-4 py-3 text-text-primary focus:outline-none focus:border-accent-primary transition-colors font-mono text-sm"
                />
              </div>
              <div>
                <label className="block text-sm text-text-secondary mb-2">Skipped Topics (comma-separated)</label>
                <input
                  type="text"
                  value={profile.skipped_topics.join(", ")}
                  onChange={(e) => {
                    const topics = e.target.value.split(",").map(s => s.trim()).filter(s => s.length > 0);
                    setProfile({ ...profile, skipped_topics: topics });
                  }}
                  className="w-full bg-bg-surface border border-white/10 rounded-lg px-4 py-3 text-text-primary focus:outline-none focus:border-accent-primary transition-colors font-mono text-sm"
                />
              </div>
            </div>

            <div className="pt-6 border-t border-white/10 flex justify-end">
              <button
                onClick={handleStart}
                disabled={loading}
                className="bg-accent-primary hover:bg-accent-primary/80 text-white font-semibold py-3 px-8 rounded-lg flex items-center gap-2 transition-all disabled:opacity-50"
              >
                {loading ? (
                  <span className="animate-pulse">Initializing Digital Twin...</span>
                ) : (
                  <>Start Interview <ArrowRight size={20} /></>
                )}
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </main>
  );
}
