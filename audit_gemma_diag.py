"""
READ-ONLY diagnostic: Test exact payloads sent to LM Studio.
Compares successful (question generation) vs failed (JSON) requests.
"""
import asyncio
import json
import sys
import time

import httpx

BASE = "http://127.0.0.1:1234/v1"
MODEL = "google/gemma-4-e4b"


async def call_chat(payload, label):
    """Send a raw chat completion request and print the outcome."""
    url = f"{BASE}/chat/completions"
    async with httpx.AsyncClient(timeout=90) as client:
        try:
            t0 = time.time()
            r = await client.post(url, json=payload)
            dt = time.time() - t0
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
            content = ""
            if r.status_code == 200:
                content = body["choices"][0]["message"]["content"]
            print(f"\n=== {label} ===")
            print(f"  HTTP {r.status_code} in {dt:.1f}s")
            print(f"  content: {repr(content[:300])}")
            print(f"  content_len: {len(content or '')}")
            if r.status_code != 200:
                print(f"  error: {str(body)[:300]}")
            return content
        except Exception as e:
            print(f"\n=== {label} ===\n  EXCEPTION: {type(e).__name__}: {e}")
            return None


# 1. Question generation (KNOWN TO WORK)
question_payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are Athena, a senior AI/ML interview specialist. Generate ONE clear, specific interview question. Do NOT include the answer. Do NOT explain the question. Output ONLY the question text. Make it conversational and professional."},
        {"role": "user", "content": "Topic: Prompt Engineering\nQuestion Type: theory\nDifficulty: Level 1 — Keep this beginner-friendly. Use simple language.\nInstruction: Ask a clear conceptual question about Prompt Engineering. The candidate should explain what it is, how it works, and why it matters.\n\nGenerate exactly one interview question:"},
    ],
    "temperature": 0.8,
    "max_tokens": 256,
}

# 2. Evaluation (KNOWN TO FAIL)
eval_payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are Athena, an expert AI interview evaluator. Evaluate the candidate's answer and return a JSON object. Be fair but rigorous. Consider technical accuracy, depth, and clarity."},
        {"role": "user", "content": 'Question: What is RAG?\nTopic: RAG\nType: theory\nDifficulty Level: 1/7\n\nCandidate\'s Answer: RAG retrieves relevant chunks.\n\nEvaluate and return JSON with this exact structure:\n{\n  "score": <float 0.0-1.0>,\n  "technical_accuracy": <float 0.0-1.0>,\n  "depth": <float 0.0-1.0>,\n  "clarity": <float 0.0-1.0>,\n  "feedback": "<2-3 sentence constructive feedback>",\n  "key_gaps": ["<gap1>", "<gap2>"],\n  "strong_points": ["<point1>"]\n}'},
    ],
    "temperature": 0.3,
    "max_tokens": 512,
}

# 3. Simple JSON request (shorter prompt)
short_json_payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are an evaluator. Return valid JSON only."},
        {"role": "user", "content": '{"score": 0.8, "feedback": "good"}'},
    ],
    "temperature": 0.3,
    "max_tokens": 512,
}

# 4. JSON with response_format json_schema (structured output attempt)
schema_payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": 'Evaluate: score 0.8 out of 1. Return JSON with keys "score" (float) and "feedback" (string).'}],
    "temperature": 0.3,
    "max_tokens": 512,
    "response_format": {
        "type": "json_schema",
        "json_schema": {
            "name": "evaluation",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "score": {"type": "number"},
                    "feedback": {"type": "string"},
                },
                "required": ["score", "feedback"],
                "additionalProperties": False,
            },
        },
    },
}

# 5. JSON with response_format text (explicit, KNOWN to previously return empty)
text_fmt_payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": 'Return JSON: {"score": 0.8, "feedback": "ok"}'}],
    "temperature": 0.3,
    "max_tokens": 512,
    "response_format": {"type": "text"},
}

# 6. Tool/function calling attempt (structured output via tools)
tool_payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "Evaluate this candidate answer: 'RAG works well'. Score it."}],
    "temperature": 0.3,
    "max_tokens": 512,
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "submit_evaluation",
                "description": "Submit an evaluation result",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "number"},
                        "feedback": {"type": "string"},
                    },
                    "required": ["score", "feedback"],
                },
            },
        }
    ],
    "tool_choice": {"type": "function", "function": {"name": "submit_evaluation"}},
}


async def main():
    print("=" * 60)
    print("GEMMA STRUCTURED OUTPUT DIAGNOSTIC")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print(f"Base:  {BASE}")

    await call_chat(question_payload, "1. QUESTION GENERATION (works in e2e)")
    await call_chat(eval_payload, "2. EVALUATION (fails in e2e)")
    await call_chat(short_json_payload, "3. SHORT JSON REQUEST")
    await call_chat(schema_payload, "4. response_format=json_schema")
    await call_chat(text_fmt_payload, "5. response_format=text")
    await call_chat(tool_payload, "6. TOOL/function calling")


if __name__ == "__main__":
    asyncio.run(main())