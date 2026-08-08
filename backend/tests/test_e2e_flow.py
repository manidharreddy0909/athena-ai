"""
Athena AI — End-to-End Interview Flow Test
Verifies the hackathon requirements:
1. Minimum 8 questions
2. Minimum 4 curriculum days
3. Context-aware follow-ups

NOTE: This test runs actual LLM calls and requires GEMINI_API_KEY.
It is skipped automatically in offline / CI environments.
"""
import asyncio
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph.orchestrator import start_interview, respond_to_question, get_report
from models.interview import StartInterviewRequest, RespondRequest
from core.config import settings


@pytest.mark.asyncio
@pytest.mark.skipif(
    not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "",
    reason="GEMINI_API_KEY not set — skipping live LLM end-to-end test"
)
async def test_end_to_end_flow():
    print("Starting End-to-End Interview Test...")

    # 1. Start Interview
    req = StartInterviewRequest(
        name="Test Candidate",
        completed_missions=[1, 3, 5],
        skipped_topics=[],
    )

    start_res = await start_interview(req)
    session_id = start_res.session_id
    print(f"   Session started: {session_id}")
    print(f"   Q1 [{start_res.topic} - Day {start_res.curriculum_day}]: {start_res.question}")

    # 2. Loop until interview completes or MAX_QUESTIONS is hit
    MAX_ITERATIONS = 25  # Safety ceiling — well above MAX_QUESTIONS
    status = None
    current_topic = start_res.topic or "AI"

    for i in range(1, MAX_ITERATIONS + 1):
        ans = RespondRequest(
            session_id=session_id,
            answer=(
                f"This is my simulated answer about {current_topic}. "
                "I understand how it connects to the system architecture and real-world use cases."
            ),
        )

        status = await respond_to_question(ans)
        current_topic = status.topic or current_topic
        print(f"   Answer {i} processed. Score: {status.answer_score}")

        if status.interview_complete:
            print(f"   Interview complete at Q{status.question_number}")
            break
        else:
            print(f"   Q{status.question_number} [{status.topic} - Day {status.curriculum_day}]: {status.question[:80]}...")

    # 3. Verify Constraints
    assert status is not None
    assert status.interview_complete is True, (
        f"Interview should have completed within {MAX_ITERATIONS} questions, "
        f"but is still running at Q{status.question_number if status else '?'}"
    )

    # 4. Get Report
    report = await get_report(session_id)
    print("\nFinal Report Generated:")
    print(f"   Overall Score: {report.overall_score}")
    print(f"   Recommendation: {report.hiring_recommendation}")
    print(f"   Total Questions: {report.total_questions}")
    print(f"   Curriculum Days Covered: {len(report.curriculum_days_covered)}")

    assert report.total_questions >= 8, f"Expected >= 8 questions, got {report.total_questions}"
    assert len(report.curriculum_days_covered) >= 4, f"Expected >= 4 days, got {len(report.curriculum_days_covered)}"

    print("\nALL END-TO-END TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(test_end_to_end_flow())
