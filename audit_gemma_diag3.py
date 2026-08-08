"""
READ-ONLY confirmatory diagnostic (larger sample):
Compares EXACT current eval/plan prompts vs SHORT+json_schema, n=5 each.
Also tests simple "say hello" sanity check to measure server stability.
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


async def call_many(payload, label, runs):
    url = f"{BASE}/chat/completions"
    empty = 0
    nonempty = 0
    errors = 0
    samples = []
    async with httpx.AsyncClient(timeout=90) as client:
        for i in range(runs):
            t0 = time.time()
            try:
                r = await client.post(url, json=payload)
                dt = time.time() - t0
                body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                if r.status_code != 200:
                    errors += 1
                    samples.append(f"    run {i+1}: HTTP {r.status_code} err={str(body)[:100]}")
                    continue
                content = body["choices"][0]["message"]["content"] or ""
                if content.strip():
                    nonempty += 1
                    samples.append(f"    run {i+1}: OK in {dt:.1f}s len={len(content)} -> {repr(content[:80])}")
                else:
                    empty += 1
                    samples.append(f"    run {i+1}: EMPTY in {dt:.1f}s")
            except Exception as e:
                errors += 1
                samples.append(f"    run {i+1}: EXC {type(e).__name__}: {e}")
    print(f"=== {label} (n={runs}) ===")
    print(f"  non-empty: {nonempty} | empty: {empty} | errors: {errors}")
    for s in samples:
        print(s)
    return nonempty


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

hello_payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "Say hello"}],
    "temperature": 0.3,
    "max_tokens": 50,
}


async def main():
    print("=" * 60)
    print("CONFIRMATORY DIAGNOSTIC (n=5 each)")
    print("=" * 60)

    print("\n--- Server sanity check ---")
    await call_many(hello_payload, "SAY HELLO (control)", runs=3)

    print("\n--- BEFORE: exact prompts, no response_format ---")
    await call_many(exact_eval, "EXACT evaluation", runs=5)
    await call_many(exact_plan, "EXACT planning", runs=5)

    print("\n--- AFTER: short prompt + json_schema ---")
    await call_many(short_eval, "SHORT eval + json_schema", runs=5)
    await call_many(short_plan, "SHORT plan + json_schema", runs=5)


if __name__ == "__main__":
    asyncio.run(main())