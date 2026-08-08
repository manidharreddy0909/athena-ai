"""
Athena AI — Interview API Routes
POST /api/v1/interview/start
POST /api/v1/interview/respond
GET  /api/v1/interview/{session_id}/report
GET  /api/v1/interview/{session_id}/status
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from models.interview import (
    StartInterviewRequest, StartInterviewResponse,
    RespondRequest, RespondResponse, FeedbackReport
)
from graph.orchestrator import start_interview, respond_to_question, get_report, _sessions

router = APIRouter()


@router.post("/interview/start", response_model=StartInterviewResponse)
async def start_interview_endpoint(request: StartInterviewRequest):
    """
    Start a new AI interview session.
    Returns the first question and session ID.
    """
    try:
        response = await start_interview(request)
        return response
    except Exception as e:
        logger.error(f"Failed to start interview: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not initialize interview session: {str(e)}"
        )


@router.post("/interview/respond", response_model=RespondResponse)
async def respond_endpoint(request: RespondRequest):
    """
    Submit a candidate's answer.
    Returns the next question or marks interview as complete.
    """
    try:
        response = await respond_to_question(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to process answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interview/{session_id}/report", response_model=FeedbackReport)
async def get_report_endpoint(session_id: str):
    """
    Get the structured feedback report for a completed interview.
    Includes recruiter intelligence dashboard data.
    """
    try:
        report = await get_report(session_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interview/{session_id}/status")
async def get_status_endpoint(session_id: str):
    """Get current interview status without generating a full report."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    state = session["state"]
    return {
        "session_id": session_id,
        "status": state.status,
        "questions_asked": state.questions_asked,
        "topics_covered": state.topics_covered,
        "curriculum_days_covered": state.curriculum_days_covered,
        "confidence_score": round(state.confidence_score, 3),
        "topic_confidence": state.topic_confidence,
        "current_topic": state.current_topic,
        "is_complete": state.status.value == "complete",
    }
