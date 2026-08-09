"""
Athena AI — Digital Twin Module
Tracks a candidate's skill evolution across multiple interview sessions.
Provides a persistent skill vector, growth trajectory, and session history.
This is an in-memory implementation (DB-ready via the session store pattern).
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


# ─── Models ──────────────────────────────────────────────────────────────────

@dataclass
class SessionSnapshot:
    """A summarized record of one completed interview session."""
    session_id: str
    domain: str
    mode: str
    timestamp: float
    overall_score: float
    total_questions: int
    topics_covered: List[str]
    curriculum_days_covered: List[int]
    topic_scores: Dict[str, float]          # topic → avg score (0–1)
    dimension_scores: Dict[str, float]      # e.g. technical_depth → 0–100
    hiring_recommendation: Optional[str] = None


@dataclass
class CandidateDigitalTwin:
    """
    Represents the persistent, evolving model of a candidate's knowledge state.
    Updated after every completed interview session.
    """
    candidate_name: str
    sessions: List[SessionSnapshot] = field(default_factory=list)
    # Aggregated skill vector: topic → running confidence (0–1)
    skill_vector: Dict[str, float] = field(default_factory=dict)
    # Tracks which topics have been practiced and how often
    topic_practice_count: Dict[str, int] = field(default_factory=dict)
    # Dimension trend history: list of (timestamp, scores_dict) tuples
    dimension_history: List[Dict[str, Any]] = field(default_factory=list)

    def update_from_session(self, snapshot: SessionSnapshot) -> None:
        """Integrate a new session snapshot into the twin's state."""
        self.sessions.append(snapshot)

        # Update skill vector with EMA (exponential moving average, alpha=0.35)
        alpha = 0.35
        for topic, score in snapshot.topic_scores.items():
            if topic in self.skill_vector:
                self.skill_vector[topic] = (
                    alpha * score + (1 - alpha) * self.skill_vector[topic]
                )
            else:
                self.skill_vector[topic] = score
            self.topic_practice_count[topic] = self.topic_practice_count.get(topic, 0) + 1

        # Record dimension history entry
        self.dimension_history.append({
            "timestamp": snapshot.timestamp,
            "session_id": snapshot.session_id,
            "domain": snapshot.domain,
            "scores": snapshot.dimension_scores,
            "overall": snapshot.overall_score,
        })

    def get_growth_trajectory(self) -> Dict[str, Any]:
        """Return metrics describing the candidate's improvement over time."""
        if not self.sessions:
            return {"trend": "no_data", "sessions_count": 0}

        scores_over_time = [s.overall_score for s in self.sessions]
        first_score = scores_over_time[0]
        latest_score = scores_over_time[-1]
        improvement = latest_score - first_score

        if len(scores_over_time) >= 2:
            mid = len(scores_over_time) // 2
            first_half = sum(scores_over_time[:mid]) / mid
            second_half = sum(scores_over_time[mid:]) / max(1, len(scores_over_time) - mid)
            trend = (
                "improving" if second_half > first_half + 3 else
                "declining" if second_half < first_half - 3 else
                "stable"
            )
        else:
            trend = "baseline"

        return {
            "trend": trend,
            "sessions_count": len(self.sessions),
            "first_score": round(first_score, 1),
            "latest_score": round(latest_score, 1),
            "improvement_delta": round(improvement, 1),
            "scores_over_time": [round(s, 1) for s in scores_over_time],
            "average_score": round(sum(scores_over_time) / len(scores_over_time), 1),
        }

    def get_weak_topics(self, threshold: float = 0.55) -> List[str]:
        """Return topics where the candidate's confidence is below threshold."""
        return [
            topic for topic, conf in sorted(
                self.skill_vector.items(), key=lambda x: x[1]
            )
            if conf < threshold
        ]

    def get_strong_topics(self, threshold: float = 0.75) -> List[str]:
        """Return topics where the candidate consistently performs well."""
        return [
            topic for topic, conf in sorted(
                self.skill_vector.items(), key=lambda x: x[1], reverse=True
            )
            if conf >= threshold
        ]

    def get_recommended_domains(self) -> List[str]:
        """Return domains to focus on based on weak topic clusters."""
        weak = self.get_weak_topics()
        # Simple heuristic: suggest repeated practice in the domain with weakest topics
        if not self.sessions:
            return []
        domain_scores: Dict[str, List[float]] = {}
        for s in self.sessions:
            domain_scores.setdefault(s.domain, []).append(s.overall_score)
        avg = {d: sum(v) / len(v) for d, v in domain_scores.items()}
        return sorted(avg, key=lambda d: avg[d])[:3]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_name": self.candidate_name,
            "sessions_count": len(self.sessions),
            "skill_vector": {k: round(v, 3) for k, v in self.skill_vector.items()},
            "topic_practice_count": self.topic_practice_count,
            "growth_trajectory": self.get_growth_trajectory(),
            "weak_topics": self.get_weak_topics(),
            "strong_topics": self.get_strong_topics(),
            "recommended_domains": self.get_recommended_domains(),
            "dimension_history": self.dimension_history,
        }


# ─── Registry ─────────────────────────────────────────────────────────────────
# In-memory store: candidate_name → CandidateDigitalTwin
# For production, this would be backed by a Postgres + Qdrant store.
_twins: Dict[str, CandidateDigitalTwin] = {}


def get_or_create_twin(candidate_name: str) -> CandidateDigitalTwin:
    """Retrieve an existing twin or create a new one."""
    if candidate_name not in _twins:
        _twins[candidate_name] = CandidateDigitalTwin(candidate_name=candidate_name)
    return _twins[candidate_name]


def update_twin_from_report(report: Dict[str, Any]) -> CandidateDigitalTwin:
    """
    Called after a session completes (report generated).
    Extracts relevant fields from the FeedbackReport dict and feeds them
    into the candidate's digital twin.
    """
    name = report.get("candidate_name", "Unknown")
    twin = get_or_create_twin(name)

    # Build topic scores from knowledge graph snapshot (0–1 scale already)
    topic_scores = report.get("knowledge_graph_snapshot", {})

    # Build dimension scores (0–100 scale)
    dimension_scores = {}
    for dim in ["technical_depth", "coding_ability", "architecture", "communication", "reasoning"]:
        val = report.get(dim)
        if isinstance(val, dict):
            dimension_scores[dim] = val.get("score", 0)
        elif isinstance(val, (int, float)):
            dimension_scores[dim] = val

    snapshot = SessionSnapshot(
        session_id=report.get("session_id", ""),
        domain=report.get("domain", "ai_ml"),
        mode=report.get("mode", "general"),
        timestamp=time.time(),
        overall_score=report.get("overall_score", 0.0),
        total_questions=report.get("total_questions", 0),
        topics_covered=report.get("topics_covered", []),
        curriculum_days_covered=report.get("curriculum_days_covered", []),
        topic_scores=topic_scores,
        dimension_scores=dimension_scores,
        hiring_recommendation=report.get("hiring_recommendation"),
    )
    twin.update_from_session(snapshot)
    return twin
