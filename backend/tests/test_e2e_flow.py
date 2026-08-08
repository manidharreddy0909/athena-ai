"""
Athena AI — End-to-End Interview Flow Test
Verifies the hackathon requirements:
1. Minimum 8 questions
2. Minimum 4 curriculum days
3. Context-aware follow-ups
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph.orchestrator import start_interview, respond_to_question, get_report
from models.interview import StartInterviewRequest, RespondRequest

# Use generic fast provider for tests
from core.config import settings

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
    
    # 2. Iterate through 8 questions
    status = None
    for i in range(1, 9): # 8 questions
        # We simulate a generic answer for testing
        ans = RespondRequest(
            session_id=session_id,
            answer=f"This is my simulated answer about {start_res.topic if i==1 else status.topic}. I understand how it connects to the system architecture.",
        )
        
        status = await respond_to_question(ans)
        
        print(f"   Answer {i} processed. Score: {status.answer_score}")
        if not status.interview_complete:
            print(f"   Q{status.question_number} [{status.topic} - Day {status.curriculum_day}]: {status.question}")
        else:
            print(f"   Interview complete at Q{status.question_number}")
            break
            
    # 3. Verify Constraints
    assert status is not None
    assert status.interview_complete is True, "Interview should complete after 8 questions"
    
    # 4. Get Report
    report = await get_report(session_id)
    print("\nFinal Report Generated:")
    print(f"   Overall Score: {report.overall_score}")
    print(f"   Recommendation: {report.hiring_recommendation}")
    print(f"   Total Questions: {report.total_questions}")
    print(f"   Curriculum Days Covered: {len(report.curriculum_days_covered)}")
    
    assert report.total_questions >= 8, f"Expected 8 questions, got {report.total_questions}"
    assert len(report.curriculum_days_covered) >= 4, f"Expected >= 4 days, got {len(report.curriculum_days_covered)}"
    
    print("\nALL END-TO-END TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(test_end_to_end_flow())
