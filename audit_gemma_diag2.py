"""
READ-ONLY diagnostic experiment (before/after):
Tests the EXACT evaluation/planning prompts (current, no response_format)
vs SHORTENED prompts with response_format=json_schema.
"""
import asyncio
import time

import httpx

BASE = "http://127.0.0.1:1234/v1"
MODEL = "google/gemma-4-e4b"

EVAL_SCHEMA = {
    "name": "answer_evaluation",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "score": {"type": "number"},
            "technical_accuracy": {"type": "number"},
            "depth": {"type": "number"},
            "clarity": {"type": "number"},
            "feedback": {"type": "string"},
            "key_gaps": {"type": "array", "items": {"type": "string"}},
            "strong_points": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["score", "technical_accuracy", "depth", "clarity", "feedback", "key_gaps", "strong_points"],
        "additionalProperties": False,
    },
}

PLAN_SCHEMA = {
    "name": "next_question_plan",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "next_topic": {"type": "string"},
            "question_type": {"type": "string", "enum": ["theory", "coding", "debugging", "architecture", "system_design", "optimization", "edge_case", "follow_up"]},
            "difficulty": {"type": "integer"},
            "rationale": {"type": "string"},
            "human_explanation": {"type": "string"},
        },
        "required": ["next_topic", "question_type", "difficulty", "rationale", "human_explanation"],
        "additionalProperties": False,
    },
}

REPORT_SCHEMA = {
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
            "hiring_recommendation": {"type": "string", "enum": ["strong_hire", "hire", "consider", "no_hire"]},
            "hiring_confidence": {"type": "string"},
            "strong_areas": {"type": "array", "items": {"type": "string"}},
            "weak_areas": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string"},
        },
        "required": ["overall_score", "technical_depth_score", "coding_score", "architecture_score", "communication_score", "reasoning_score", "hiring_recommendation", "hiring_confidence", "strong_areas", "weak_areas", "summary"],
        "additionalProperties": False,
    },
}


async def call(payload, label, runs=1):
    url = f"{BASE}/chat/completions"
    results = []
    async with httpx.AsyncClient(timeout=90) as client:
        for i in range(runs):
            t0 = time.time()
            try:
                r = await client.post(url, json=payload)
                dt = time.time() - t0
                body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                content = ""
                if r.status_code == 200:
                    content = body["choices"][0]["message"]["content"] or ""
                results.append((r.status_code, content, dt))
            except Exception as e:
                results.append(("EXC", "", 0))
                print(f"  run {i+1}: EXC {type(e).__name__}: {e}")
    ok = sum(1 for s, c, _ in results if s == 200 and c.strip())
    print(f"\n=== {label} (runs={runs}) ===")
    print(f"  non-empty success: {ok}/{runs}")
    for i, (s, c, dt) in enumerate(results):
        print(f"  run {i+1}: HTTP {s} in {dt:.1f}s len={len(c or '')} content={repr((c or '')[:120])}")
    return results


# ── BEFORE: EXACT current prompts, NO response_format ──

exact_eval = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are Athena, an expert AI interview evaluator. Evaluate the candidate's answer and return a JSON object. Be fair but rigorous. Consider technical accuracy, depth, and clarity."},
        {"role": "user", "content": 'Question: What is RAG?\nTopic: RAG\nType: theory\nDifficulty Level: 1/7\n\nCandidate\'s Answer: RAG retrieves relevant chunks from a vector database and augments generation.\n\nEvaluate and return JSON with this exact structure:\n{\n  "score": <float 0.0-1.0>,\n  "technical_accuracy": <float 0.0-1.0>,\n  "depth": <float 0.0-1.0>,\n  "clarity": <float 0.0-1.0>,\n  "feedback": "<2-3 sentence constructive feedback>",\n  "key_gaps": ["<gap1>", "<gap2>"],\n  "strong_points": ["<point1>"]\n}'},
    ],
    "temperature": 0.3,
    "max_tokens": 512,
}

short_eval = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are an expert AI interview evaluator. Be fair but rigorous."},
        {"role": "user", "content": "Question: What is RAG?\nTopic: RAG\nCandidate's Answer: RAG retrieves relevant chunks from a vector database and augments generation.\n\nReturn a single JSON object conforming exactly to the provided schema."},
    ],
    "temperature": 0.1,
    "max_tokens": 512,
    "response_format": {"type": "json_schema", "json_schema": EVAL_SCHEMA},
}

exact_plan = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are the Chief Interview Agent for Athena AI. You must decide what to ask next based on the candidate's performance. Return a JSON object with your decision."},
        {"role": "user", "content": 'Interview state:\n- Questions asked: 3\n- Minimum required: 8\n- Topics covered: ["Prompt Engineering", "RAG"]\n- Curriculum days covered: [1, 3]\n- Days still needed: 2\n- Weak topics: ["Embeddings", "Chunking"]\n- Current topic: RAG\n- Confidence score: 0.50\n- Consecutive correct: 1\n- Consecutive wrong: 1\n\nRules:\n1. If days_needed > 0, prioritize topics from uncovered days\n2. If confidence < 0.4, drop difficulty and revisit fundamentals\n3. If consecutive_correct >= 3, increase difficulty\n4. If consecutive_wrong >= 2, decrease difficulty or change topic\n5. Never repeat recently covered topics unless doing follow-up\n\nReturn JSON:\n{\n  "next_topic": "<topic from the curriculum>",\n  "question_type": "<theory|coding|debugging|architecture|system_design|optimization|edge_case|follow_up>",\n  "difficulty": <1-7>,\n  "rationale": "<why this decision>",\n  "human_explanation": "<short explanation for the candidate-facing UI>"\n}'},
    ],
    "temperature": 0.4,
    "max_tokens": 512,
}

short_plan = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are the Chief Interview Agent. Decide the next interview question."},
        {"role": "user", "content": "Interview state: questions_asked=3, days_covered=[1,3], days_needed=2, weak_topics=[Embeddings, Chunking], current_topic=RAG, consecutive_correct=1, consecutive_wrong=1.\n\nReturn a single JSON object conforming exactly to the provided schema."},
    ],
    "temperature": 0.1,
    "max_tokens": 512,
    "response_format": {"type": "json_schema", "json_schema": PLAN_SCHEMA},
}

exact_report = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are Athena AI's evaluation engine. Generate a structured assessment of a technical interview. Return valid JSON."},
        {"role": "user", "content": 'Candidate: Test\nTopics covered: ["RAG", "Embeddings", "Chunking"]\nCurriculum days covered: [3, 4, 5]\nAverage score: 0.50\nTotal questions: 8\n\nQ&A Summary:\nQ1 [RAG]: What is RAG?\n  Answer score: 0.50\n\nGenerate a comprehensive assessment as JSON:\n{\n  "overall_score": <0-100>,\n  "technical_depth_score": <0-100>,\n  "coding_score": <0-100>,\n  "architecture_score": <0-100>,\n  "communication_score": <0-100>,\n  "reasoning_score": <0-100>,\n  "hiring_recommendation": "<strong_hire|hire|consider|no_hire>",\n  "hiring_confidence": "<high|medium|low>",\n  "strong_areas": ["<area1>", "<area2>"],\n  "weak_areas": ["<area1>", "<area2>"],\n  "summary": "<2-3 sentence executive summary>"\n}'},
    ],
    "temperature": 0.2,
    "max_tokens": 1024,
}

short_report = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are an interview assessment engine."},
        {"role": "user", "content": "Candidate: Test\nTopics covered: [RAG, Embeddings, Chunking]\nCurriculum days covered: [3,4,5]\nAverage score: 0.50\nTotal questions: 8\nQ1 [RAG]: What is RAG? score 0.50\n\nReturn a single JSON object conforming exactly to the provided schema."},
    ],
    "temperature": 0.1,
    "max_tokens": 1024,
    "response_format": {"type": "json_schema", "json_schema": REPORT_SCHEMA},
}


async def main():
    print("=" * 60)
    print("BEFORE vs AFTER: structured output experiment")
    print("=" * 60)

    print("\n############ BEFORE (no response_format, exact complex prompt) ############")
    await call(exact_eval, "EXACT evaluation (current)", runs=3)
    await call(exact_plan, "EXACT planning (current)", runs=3)
    await call(exact_report, "EXACT report (current)", runs=2)

    print("\n############ AFTER (short prompt + json_schema) ############")
    await call(short_eval, "SHORT eval + json_schema", runs=3)
    await call(short_plan, "SHORT plan + json_schema", runs=3)
    await call(short_report, "SHORT report + json_schema", runs=2)


if __name__ == "__main__":
    asyncio.run(main())