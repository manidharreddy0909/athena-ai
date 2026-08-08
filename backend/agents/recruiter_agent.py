"""
Athena AI — Recruiter Intelligence Agent (Phase 11)
Generates hiring-manager-grade intelligence from the interview session:
- Executive summary (1-paragraph elevator pitch verdict)
- Red flags (blockers / concerns)
- Green flags (standout strengths)
- Culture/communication fit notes
"""
from typing import Dict, Any
from loguru import logger
from core.llm import chat_completion_with_retry, parse_json_response, LogicRole
from models.interview import InterviewState


async def generate_recruiter_intelligence(state: InterviewState) -> Dict[str, Any]:
    """
    Analyse the full interview session and return recruiter-grade intelligence.
    Returns a dict with: executive_summary, red_flags, green_flags, culture_fit_notes
    """
    if not state.qa_history:
        return {
            "executive_summary": "Insufficient data — interview was too short.",
            "red_flags": [],
            "green_flags": [],
            "culture_fit_notes": "",
        }

    avg_score = (
        sum(qa.get("score", 0.5) for qa in state.qa_history) / len(state.qa_history)
        if state.qa_history else 0.5
    )

    # Build a compact transcript for context
    transcript_lines = []
    for i, qa in enumerate(state.qa_history[:12], 1):
        score = qa.get("score", 0.5)
        topic = qa.get("topic", "?")
        qtype = qa.get("question_type", "theory")
        transcript_lines.append(
            f"Q{i} [{topic}/{qtype}]: score={score:.2f} | {qa.get('feedback', '')[:120]}"
        )
    transcript_summary = "\n".join(transcript_lines)

    rec_hint = "strong_hire" if avg_score >= 0.80 else ("hire" if avg_score >= 0.65 else ("consider" if avg_score >= 0.45 else "no_hire"))

    messages = [
        {
            "role": "user",
            "content": f"""You are a Principal Technical Recruiter writing an intelligence brief for the Hiring Manager.

Candidate: {state.candidate.name}
Domain: {state.domain}
Interview Mode: {state.mode}
Total Questions: {state.questions_asked}
Average Score: {avg_score:.2f}/1.0
Hiring Signal: {rec_hint}
Topics Covered: {', '.join(state.topics_covered[:10])}

Interview Transcript Summary:
{transcript_summary}

Write a structured recruiter intelligence brief. Return valid JSON only:
{{
  "executive_summary": "<3-4 sentence hiring manager brief: who is this candidate, what are their strengths, should we hire them and why>",
  "red_flags": ["<specific technical or behavioral concern 1>", "<concern 2>"],
  "green_flags": ["<specific standout strength 1>", "<strength 2>", "<strength 3>"],
  "culture_fit_notes": "<1-2 sentences on communication style, collaboration signals, and seniority impression>"
}}

Be specific, honest, and actionable. Avoid generic statements."""
        }
    ]

    try:
        result_str = await chat_completion_with_retry(
            messages,
            temperature=0.3,
            max_tokens=600,
            role=LogicRole.REPORTER,
        )
        data = parse_json_response(result_str)
        logger.info(f"🎯 Recruiter intelligence generated for {state.candidate.name}")
        return {
            "executive_summary": str(data.get("executive_summary", "")),
            "red_flags": data.get("red_flags", []),
            "green_flags": data.get("green_flags", []),
            "culture_fit_notes": str(data.get("culture_fit_notes", "")),
        }
    except Exception as e:
        logger.error(f"Recruiter intelligence failed: {e}")
        return {
            "executive_summary": f"{state.candidate.name} completed a {state.questions_asked}-question interview with an average score of {avg_score:.0%}.",
            "red_flags": [],
            "green_flags": [],
            "culture_fit_notes": "",
        }
