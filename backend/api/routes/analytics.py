"""
Athena AI — Analytics API Routes (Phase 13)
Exposes per-session analytics, aggregate statistics, and performance trends.
GET /api/v1/analytics/{session_id}/summary
GET /api/v1/analytics/global/stats
"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from graph.orchestrator import _sessions

router = APIRouter()


@router.get("/analytics/{session_id}/summary")
async def get_session_analytics(session_id: str):
    """
    Return a detailed performance analytics summary for a specific session.
    Includes per-topic breakdown, time trends, and scoring dimensions.
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    state = session["state"]
    qa_history = state.qa_history

    if not qa_history:
        return {"session_id": session_id, "message": "No Q&A data yet.", "analytics": {}}

    scores = [qa.get("score", 0.5) for qa in qa_history]
    avg_score = sum(scores) / len(scores)
    
    # Score trend: split into first-half and second-half averages
    mid = max(1, len(scores) // 2)
    first_half_avg = sum(scores[:mid]) / mid
    second_half_avg = sum(scores[mid:]) / max(1, len(scores) - mid)
    trend = "improving" if second_half_avg > first_half_avg + 0.05 else (
        "declining" if second_half_avg < first_half_avg - 0.05 else "stable"
    )

    # Per-topic performance
    topic_perf: dict = {}
    for qa in qa_history:
        t = qa.get("topic", "Unknown")
        s = qa.get("score", 0.5)
        if t not in topic_perf:
            topic_perf[t] = {"scores": [], "count": 0}
        topic_perf[t]["scores"].append(s)
        topic_perf[t]["count"] += 1

    topic_summary = {
        t: {
            "avg_score": round(sum(v["scores"]) / v["count"], 3),
            "attempts": v["count"],
            "status": "strong" if sum(v["scores"]) / v["count"] >= 0.70 else (
                "weak" if sum(v["scores"]) / v["count"] < 0.50 else "moderate"
            ),
        }
        for t, v in topic_perf.items()
    }

    # Question type distribution
    qtype_dist: dict = {}
    for qa in qa_history:
        qtype = qa.get("question_type", "theory")
        qtype_dist[qtype] = qtype_dist.get(qtype, 0) + 1

    return {
        "session_id": session_id,
        "candidate_name": state.candidate.name,
        "domain": state.domain,
        "mode": state.mode,
        "language": state.language,
        "analytics": {
            "total_questions": state.questions_asked,
            "topics_covered": len(state.topics_covered),
            "curriculum_days_covered": len(state.curriculum_days_covered),
            "avg_score": round(avg_score, 3),
            "score_trend": trend,
            "first_half_avg": round(first_half_avg, 3),
            "second_half_avg": round(second_half_avg, 3),
            "topic_performance": topic_summary,
            "question_type_distribution": qtype_dist,
            "consecutive_correct": state.consecutive_correct,
            "consecutive_wrong": state.consecutive_wrong,
        }
    }


@router.get("/analytics/global/stats")
async def get_global_stats():
    """
    Return aggregate statistics across all active sessions.
    Useful for monitoring and platform dashboards.
    """
    total_sessions = len(_sessions)
    active = sum(1 for s in _sessions.values() if s["state"].status.value == "in_progress")
    completed = sum(1 for s in _sessions.values() if s["state"].status.value == "complete")

    all_scores = []
    domain_counts: dict = {}
    for s in _sessions.values():
        state = s["state"]
        for qa in state.qa_history:
            if qa.get("score") is not None:
                all_scores.append(qa["score"])
        domain_counts[state.domain] = domain_counts.get(state.domain, 0) + 1

    global_avg = round(sum(all_scores) / len(all_scores), 3) if all_scores else 0.0

    return {
        "total_sessions": total_sessions,
        "active_sessions": active,
        "completed_sessions": completed,
        "total_answers_evaluated": len(all_scores),
        "global_avg_score": global_avg,
        "domain_distribution": domain_counts,
    }
