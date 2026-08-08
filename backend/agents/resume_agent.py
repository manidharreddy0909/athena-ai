"""
Athena AI — Resume & JD Intelligence Agent (Phase 10)
Analyzes candidate resumes and job descriptions to tailor the interview.
Extracts key technical skills, experience gaps, and maps them to the domain graph.
"""
from typing import Dict, List, Any
from loguru import logger
from core.llm import chat_completion_with_retry, parse_json_response, LogicRole


async def analyze_resume_and_jd(
    resume_text: str,
    jd_text: str,
    domain_engine: Any,
) -> Dict[str, Any]:
    """
    Analyze the candidate's resume against the Job Description.
    Returns targeted topics for the interview to focus on.
    """
    if not resume_text and not jd_text:
        return {
            "focus_topics": [],
            "identified_gaps": [],
            "candidate_strengths": [],
            "context_summary": ""
        }

    all_domain_topics = domain_engine.get_all_topics()
    domain_name = domain_engine.config.get("name", "Technology")

    messages = [
        {
            "role": "user",
            "content": f"""You are the Chief Talent Officer. Analyze the candidate's Resume and the Job Description.
We need to design a highly tailored technical interview for the '{domain_name}' domain.

Available Domain Topics: {', '.join(all_domain_topics)}

Resume:
{resume_text[:2500] if resume_text else '(No resume provided)'}

Job Description:
{jd_text[:2500] if jd_text else '(No job description provided)'}

Identify:
1. Candidate Strengths: What do they already know well?
2. Experience Gaps: What does the JD require that is missing or weak in the resume?
3. Focus Topics: Select 3-5 topics from the 'Available Domain Topics' list that we MUST test during the interview to validate this candidate for this specific role.

Respond with valid JSON only:
{{
  "candidate_strengths": ["<strength 1>", "<strength 2>"],
  "identified_gaps": ["<gap 1>", "<gap 2>"],
  "focus_topics": ["<topic 1 from available list>", "<topic 2>"],
  "context_summary": "<2 sentence summary of how we should approach this interview>"
}}"""
        }
    ]

    try:
        result_str = await chat_completion_with_retry(
            messages,
            temperature=0.2,
            max_tokens=400,
            role=LogicRole.PROFILE_ANALYZER,
        )
        data = parse_json_response(result_str)
        
        # Ensure focus topics actually exist in our graph
        valid_focus_topics = [
            t for t in data.get("focus_topics", [])
            if t in all_domain_topics
        ]
        
        # Fallback to strengths/gaps if topics didn't match perfectly
        if not valid_focus_topics and all_domain_topics:
            valid_focus_topics = all_domain_topics[:3]
            
        data["focus_topics"] = valid_focus_topics
        logger.info(f"📄 Resume/JD Analysis complete. Focus topics: {valid_focus_topics}")
        return data
        
    except Exception as e:
        logger.error(f"Resume analysis failed: {e}")
        return {
            "focus_topics": [],
            "identified_gaps": [],
            "candidate_strengths": [],
            "context_summary": ""
        }
