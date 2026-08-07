// Athena AI — Backend API Client
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CandidateProfile {
  name: string;
  completed_missions: number[];
  skipped_topics: string[];
  learning_signals?: Record<string, number>;
}

export interface ReasoningTrace {
  weak_node?: string;
  dependency_path: string[];
  proposing_agent?: string;
  human_explanation: string;
}

export interface StartResponse {
  session_id: string;
  candidate_id: string;
  question_number: number;
  question: string;
  question_type: string;
  topic: string;
  curriculum_day?: number;
  difficulty_level: number;
  reasoning_trace: ReasoningTrace;
  total_questions_planned: number;
  message: string;
}

export interface RespondResponse {
  session_id: string;
  question_number: number;
  question?: string;
  question_type?: string;
  topic?: string;
  curriculum_day?: number;
  difficulty_level?: number;
  reasoning_trace?: ReasoningTrace;
  answer_score?: number;
  answer_feedback?: string;
  interview_complete: boolean;
  questions_remaining: number;
  message: string;
}

export interface DimensionScore {
  score: number;
  notes: string;
}

export interface FeedbackReport {
  session_id: string;
  candidate_id: string;
  candidate_name: string;
  overall_score: number;
  technical_depth: DimensionScore;
  coding_ability: DimensionScore;
  architecture: DimensionScore;
  communication: DimensionScore;
  reasoning: DimensionScore;
  hiring_confidence: string;
  hiring_recommendation: string;
  strong_areas: string[];
  weak_areas: string[];
  topics_covered: string[];
  curriculum_days_covered: number[];
  total_questions: number;
  knowledge_graph_snapshot: Record<string, number>;
  learning_plan_30_day: string[];
  learning_plan_60_day: string[];
  learning_plan_90_day: string[];
}

export const api = {
  async startInterview(profile: CandidateProfile): Promise<StartResponse> {
    const res = await fetch(`${API_BASE}/api/v1/interview/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    if (!res.ok) throw new Error(`Start failed: ${res.statusText}`);
    return res.json();
  },

  async respond(sessionId: string, answer: string): Promise<RespondResponse> {
    const res = await fetch(`${API_BASE}/api/v1/interview/respond`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, answer }),
    });
    if (!res.ok) throw new Error(`Respond failed: ${res.statusText}`);
    return res.json();
  },

  async getReport(sessionId: string): Promise<FeedbackReport> {
    const res = await fetch(`${API_BASE}/api/v1/interview/${sessionId}/report`);
    if (!res.ok) throw new Error(`Report failed: ${res.statusText}`);
    return res.json();
  },

  async getStatus(sessionId: string) {
    const res = await fetch(`${API_BASE}/api/v1/interview/${sessionId}/status`);
    if (!res.ok) throw new Error(`Status failed: ${res.statusText}`);
    return res.json();
  },
};
