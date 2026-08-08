"""
Athena AI — Feedback & Learning Planner Agent
Generates the structured recruiter report and personalized learning roadmap
"""
import json
from core.llm import chat_completion, parse_json_response
from models.interview import (
    FeedbackReport, DimensionScore, HiringRecommendation, InterviewState
)
from loguru import logger
from datetime import datetime


REPORT_JSON_SCHEMA = {
    "name": "interview_assessment",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "overall_score": {"type": "integer"},
            "technical_depth_score": {"type": "integer"},
            "coding_score": {"type": "integer"},
            "architecture_score": {"type": "integer"},
            "communication_score": {"type": "integer"},
            "reasoning_score": {"type": "integer"},
            "hiring_recommendation": {
                "type": "string",
                "enum": ["strong_hire", "hire", "consider", "no_hire"],
            },
            "hiring_confidence": {"type": "string"},
            "strong_areas": {"type": "array", "items": {"type": "string"}},
            "weak_areas": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string"},
        },
        "required": [
            "overall_score", "technical_depth_score", "coding_score",
            "architecture_score", "communication_score", "reasoning_score",
            "hiring_recommendation", "hiring_confidence",
            "strong_areas", "weak_areas", "summary",
        ],
        "additionalProperties": False,
    },
}


LEARNING_RESOURCES = {
    "RAG": {
        "docs": "LangChain RAG documentation",
        "project": "Build a document Q&A system with LangChain + Qdrant",
        "repo": "github.com/langchain-ai/rag-from-scratch",
        "paper": "REALM: Retrieval-Augmented Language Model Pre-Training",
    },
    "Embeddings": {
        "docs": "OpenAI Embeddings guide",
        "project": "Build a semantic search engine from scratch",
        "repo": "github.com/openai/openai-cookbook",
        "paper": "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    },
    "Vector Database": {
        "docs": "Qdrant documentation — Getting Started",
        "project": "Index and search 1 million documents with Qdrant",
        "repo": "github.com/qdrant/qdrant",
        "paper": "Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs",
    },
    "Agentic AI": {
        "docs": "LangGraph documentation — Agents",
        "project": "Build a multi-agent research assistant",
        "repo": "github.com/langchain-ai/langgraph",
        "paper": "ReAct: Synergizing Reasoning and Acting in Language Models",
    },
    "Prompt Engineering": {
        "docs": "OpenAI Prompt Engineering Guide",
        "project": "Build a prompt optimization pipeline",
        "repo": "github.com/dair-ai/Prompt-Engineering-Guide",
        "paper": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
    },
    "MCP": {
        "docs": "Model Context Protocol specification",
        "project": "Build an MCP server for a custom tool",
        "repo": "github.com/anthropics/anthropic-cookbook",
        "paper": "Tool use and MCP integration patterns",
    },
}


async def generate_learning_plan(weak_topics: list[str]) -> dict:
    """Generate a 30/60/90-day learning plan for weak topics."""
    plan = {"30_day": [], "60_day": [], "90_day": []}

    for topic in weak_topics[:5]:  # focus on top 5 weak areas
        resources = LEARNING_RESOURCES.get(topic, {})
        if resources:
            plan["30_day"].append(f"Study {topic}: {resources.get('docs', '')}")
            plan["30_day"].append(f"Project: {resources.get('project', '')}")
            plan["60_day"].append(f"Read: {resources.get('paper', '')}")
            plan["60_day"].append(f"Explore: {resources.get('repo', '')}")

    plan["90_day"] = [
        "Build an end-to-end production AI system deploying RAG + Agents",
        "Complete a system design mock interview preparation",
        "Contribute to an open-source AI project",
        "Create a portfolio project demonstrating production AI skills",
    ]

    return plan


async def generate_report(state: InterviewState) -> FeedbackReport:
    """
    Generate the complete recruiter intelligence report.
    """
    logger.info(f"📊 Generating report for session {state.session_id}")

    qa_history = state.qa_history
    scores = [qa.get("score", 0.5) for qa in qa_history if qa.get("score") is not None]
    avg_score = sum(scores) / len(scores) if scores else 0.5

    # Ask LLM to analyze the full interview
    qa_summary = "\n".join([
        f"Q{i+1} [{qa.get('topic')}]: {qa.get('question', '')[:100]}\n  Answer score: {qa.get('score', 0):.2f}"
        for i, qa in enumerate(qa_history)
    ])

    messages = [
        {
            "role": "user",
            "content": f"""You are an interview assessment engine. Analyze this interview and return a JSON assessment.

Candidate: {state.candidate.name}
Topics covered: {', '.join(state.topics_covered[:10])}
Curriculum days covered: {state.curriculum_days_covered}
Average score: {avg_score:.2f}
Total questions: {state.questions_asked}

{qa_summary[:800]}

Respond with valid JSON only:
{{"overall_score": <int 0-100>, "technical_depth_score": <int 0-100>, "coding_score": <int 0-100>, "architecture_score": <int 0-100>, "communication_score": <int 0-100>, "reasoning_score": <int 0-100>, "hiring_recommendation": "hire"|"consider"|"no_hire", "hiring_confidence": "high"|"medium"|"low", "strong_areas": [<topics>], "weak_areas": [<topics>], "summary": "<2 sentence summary>"}}""",
        },
    ]

    try:
        from core.llm import chat_completion_with_retry, LogicRole
        result_str = await chat_completion_with_retry(
            messages, temperature=0.1, max_tokens=512,
            json_mode=False, use_breath_layer=True, role=LogicRole.REPORTER
        )
        assessment = parse_json_response(result_str)
    except Exception as e:
        logger.error(f"Report generation LLM failed: {e}")
        assessment = {
            "overall_score": round(avg_score * 100, 1),
            "technical_depth_score": round(avg_score * 100, 1),
            "coding_score": round(avg_score * 90, 1),
            "architecture_score": round(avg_score * 95, 1),
            "communication_score": round(avg_score * 85, 1),
            "reasoning_score": round(avg_score * 90, 1),
            "hiring_recommendation": "hire" if avg_score >= 0.6 else "consider",
            "hiring_confidence": "medium",
            "strong_areas": state.topics_covered[:3],
            "weak_areas": [],
            "summary": f"Candidate completed {state.questions_asked} questions across {len(state.topics_covered)} topics.",
        }

    # Generate learning plan
    weak_topics = assessment.get("weak_areas", [])
    learning_plan = await generate_learning_plan(weak_topics)

    # Build hiring recommendation enum
    rec_str = assessment.get("hiring_recommendation", "consider")
    try:
        recommendation = HiringRecommendation(rec_str)
    except ValueError:
        recommendation = HiringRecommendation.CONSIDER

    report = FeedbackReport(
        session_id=state.session_id,
        candidate_id=state.candidate.candidate_id,
        candidate_name=state.candidate.name,
        completed_at=datetime.utcnow(),
        overall_score=assessment.get("overall_score", 50.0),
        technical_depth=DimensionScore(
            score=assessment.get("technical_depth_score", 50.0),
            notes="Based on theory and concept questions",
        ),
        coding_ability=DimensionScore(
            score=assessment.get("coding_score", 50.0),
            notes="Based on coding and debugging questions",
        ),
        architecture=DimensionScore(
            score=assessment.get("architecture_score", 50.0),
            notes="Based on architecture and system design questions",
        ),
        communication=DimensionScore(
            score=assessment.get("communication_score", 50.0),
            notes="Based on clarity and depth of explanations",
        ),
        reasoning=DimensionScore(
            score=assessment.get("reasoning_score", 50.0),
            notes="Based on follow-up responses and reasoning depth",
        ),
        hiring_confidence=assessment.get("hiring_confidence", "medium"),
        hiring_recommendation=recommendation,
        strong_areas=assessment.get("strong_areas", []),
        weak_areas=assessment.get("weak_areas", []),
        topics_covered=state.topics_covered,
        curriculum_days_covered=state.curriculum_days_covered,
        total_questions=state.questions_asked,
        knowledge_graph_snapshot=state.topic_confidence,
        learning_plan_30_day=learning_plan["30_day"],
        learning_plan_60_day=learning_plan["60_day"],
        learning_plan_90_day=learning_plan["90_day"],
        qa_transcript=state.qa_history,
    )

    return report
