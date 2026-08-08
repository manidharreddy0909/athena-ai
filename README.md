# 🦉 Athena AI — Autonomous Interview Intelligence Platform

> A production-grade AI Interview Operating System that conducts adaptive, explainable, multilingual technical interviews using multi-agent orchestration, knowledge graphs, and candidate digital twins.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-31%20passing-brightgreen)]()

---

## 🎯 What is Athena AI?

Athena AI is not a chatbot. It is an **AI Interview Operating System** built on:

- 🧠 **Adaptive Knowledge Graph** — tracks candidate mastery per topic, drives question selection
- 🤖 **Multi-Agent Orchestration** — Profile Analyzer → Question Generator → Evaluator → Socratic Engine → Recruiter Reporter
- 🔍 **Socratic Follow-up Intelligence** — probes partial answers instead of robotically moving on
- 🌍 **Multilingual Support** — conduct interviews in Hindi, Spanish, French, Telugu, Arabic, and 30+ languages
- 📄 **Resume & JD Intelligence** — analyzes candidate resume against job description to focus the interview
- 🎙️ **Voice I/O** — Gemini-powered STT/TTS for hands-free voice interviews
- 📊 **Recruiter Intelligence Reports** — executive summaries, red/green flags, culture-fit notes, 30/60/90-day learning plans
- 🔒 **Security-First** — request tracing, security headers, no secrets in code
- ⚡ **Performance** — LLM response cache, retry-with-backoff, graceful degradation

---

## 🏗️ Architecture

```
[Candidate Input]
       │
       ▼
[Profile Analyzer] ──── Resume/JD Intelligence ────► [Knowledge Graph Pre-load]
       │
       ▼
[LangGraph Orchestrator]
       │
       ├─► [node_profile_analysis]  → picks initial topic, builds reasoning trace
       ├─► [node_generate_question] → LLM generates question (language-aware)
       ├─► [node_evaluate_answer]   → Deep evaluation (score + dimensions)
       ├─► [node_memory_update]     → Updates KG, Digital Twin, Memory Engine
       └─► [node_plan_next]         → Socratic follow-up OR new topic planning
                                           │
                                    [Complete?]
                                           │
                                           ▼
                               [node_generate_report]
                                           │
                              [Recruiter Intelligence]
                                           │
                                   [FeedbackReport]
```

**Tech Stack:**
| Layer | Technology |
|---|---|
| Frontend | Next.js 14, Tailwind CSS, shadcn/ui, React Flow, Recharts |
| Backend | FastAPI, LangGraph, Pydantic v2, Python 3.12 |
| AI / LLM | Gemini 2.5 Pro/Flash (via Google AI) |
| Memory | BREATH AI Layer (persistent), Qdrant (semantic search) |
| Database | PostgreSQL + SQLAlchemy async |
| Voice | Gemini STT/TTS |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- `GEMINI_API_KEY` (required for AI features)

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate        # macOS/Linux

pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env and set GEMINI_API_KEY

uvicorn main:app --reload --port 8000
```

API available at: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: http://localhost:3000

---

## 📡 API Reference

### Start Interview
```http
POST /api/v1/interview/start
Content-Type: application/json

{
  "name": "Alice Chen",
  "domain": "ai_ml",           // ai_ml | software_engineering | data_engineering | cloud_devops
  "mode": "general",           // general | coding | system_design
  "language": "en",            // en | hi | es | fr | de | zh | te | ar | ...
  "resume_text": "...",        // optional: candidate's resume
  "jd_text": "..."             // optional: job description
}
```

### Submit Answer
```http
POST /api/v1/interview/respond
{
  "session_id": "sess_abc123",
  "answer": "My answer here..."
}
```

### Get Report
```http
GET /api/v1/interview/{session_id}/report
```

### Session Analytics
```http
GET /api/v1/analytics/{session_id}/summary
GET /api/v1/analytics/global/stats
```

### Voice
```http
POST /api/v1/voice/stt          # Speech to text
POST /api/v1/voice/tts          # Text to speech
```

---

## 🌍 Supported Domains

| Domain | Key Topics |
|---|---|
| **AI / ML** (default) | RAG, Embeddings, Transformers, Agentic AI, Vector DBs, Prompt Engineering |
| **Software Engineering** | System Design, Data Structures, Algorithms, Architecture Patterns |
| **Data Engineering** | Spark, Kafka, dbt, Data Pipelines, Warehousing |
| **Cloud / DevOps** | Kubernetes, CI/CD, Terraform, Observability |

---

## 🎙️ Supported Languages

30+ languages including English, Hindi, Spanish, French, German, Chinese, Arabic, Telugu, Tamil, Portuguese, Japanese, Korean, Russian, and more.

Set `language` in the start request to the ISO 639-1 code (e.g., `"hi"` for Hindi).

---

## 🧪 Tests

```bash
cd backend
# Fast offline tests (no API key required)
python -m pytest tests/test_basic.py tests/test_llm_parsing.py tests/test_providers.py tests/test_phases_8_to_16.py -v

# All tests (e2e requires GEMINI_API_KEY)
python -m pytest tests/ -v
```

Current test coverage: **31 unit tests passing**, 1 e2e test (requires live API key).

---

## 🔐 Security

- All API responses include security headers (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, etc.)
- Request tracing via `X-Request-ID` header
- No secrets in code — all keys loaded from `.env`
- CORS configured via `settings.CORS_ORIGINS`

---

## 📊 Interview Flow

1. **Profile Analysis** — Resume/JD analyzed, knowledge graph seeded with candidate signals
2. **Question Generation** — LLM generates domain-specific, language-aware questions
3. **Answer Evaluation** — Deep multi-dimensional scoring (technical accuracy, depth, clarity, practical experience)
4. **Socratic Follow-up** — If score is 0.45–0.74, Athena probes deeper instead of moving on
5. **Adaptive Planning** — Next topic chosen by Chief Interview Agent based on weak areas, curriculum coverage, streak
6. **Completion** — Interview ends when MIN_QUESTIONS + MIN_CURRICULUM_DAYS are satisfied, or MAX_QUESTIONS is reached
7. **Report Generation** — Full recruiter intelligence report with executive summary, red/green flags, learning plan

---

## 📁 Project Structure

```
athena-ai/
├── backend/
│   ├── agents/
│   │   ├── interview_agents.py     # Question generator + planner
│   │   ├── socratic_engine.py      # Follow-up intelligence + deep evaluation
│   │   ├── feedback_agent.py       # Report generation
│   │   ├── recruiter_agent.py      # Recruiter intelligence (Phase 11)
│   │   └── resume_agent.py         # Resume/JD analysis (Phase 10)
│   ├── api/routes/
│   │   ├── interview.py            # Core interview endpoints
│   │   ├── analytics.py            # Analytics endpoints (Phase 13)
│   │   └── voice.py                # Voice endpoints (Phase 7)
│   ├── core/
│   │   ├── llm.py                  # Provider-agnostic LLM client
│   │   ├── multilingual.py         # Translation + language detection (Phase 8)
│   │   ├── voice_service.py        # STT/TTS service (Phase 7)
│   │   ├── cache.py                # LLM response cache (Phase 17)
│   │   └── config.py               # Settings + env vars
│   ├── graph/
│   │   └── orchestrator.py         # LangGraph multi-node interview graph
│   ├── knowledge/
│   │   ├── knowledge_graph.py      # Curriculum-aware directed graph
│   │   └── domain_engine.py        # Multi-domain configurations (Phase 6)
│   ├── memory/
│   │   ├── memory_engine.py        # Session memory manager
│   │   └── semantic_memory.py      # Qdrant vector search
│   ├── models/
│   │   └── interview.py            # Pydantic models for all entities
│   └── tests/
│       ├── test_basic.py
│       ├── test_llm_parsing.py
│       ├── test_providers.py
│       ├── test_phases_8_to_16.py  # Phases 8-16 unit tests
│       └── test_e2e_flow.py        # End-to-end integration test
└── frontend/
    └── ...                         # Next.js 14 frontend
```

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with 🦉 by Athena AI — Where every interview is a masterclass.*
