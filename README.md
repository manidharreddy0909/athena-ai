# 🦉 Athena AI — Autonomous Interview Intelligence Platform

> An AI Interview Operating System that conducts adaptive, explainable technical interviews using multi-agent debate, knowledge graphs, and candidate digital twins.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-blue)](https://langchain-ai.github.io/langgraph/)

---

## 🎯 What is Athena AI?

Athena AI is not a chatbot. It is an **AI Interview Operating System** that:

- 🧠 **Understands the candidate** via a live-updating Digital Twin
- 🗺️ **Maps knowledge** using a directed curriculum Knowledge Graph
- 🤖 **Debates internally** using 8 specialist agents before asking each question
- 💡 **Explains every decision** with full reasoning traces (Explainable AI)
- 📊 **Generates recruiter reports** with dimensional scoring and learning roadmaps

---

## 🏗️ Architecture

```
Candidate → Profile Analyzer → Knowledge Graph → Memory Engine
         → Multi-Agent Debate → Question Generator → Interview Conductor
         → Evaluation Agent → Feedback Engine → Recruiter Report
```

**Tech Stack:**
- **Frontend**: Next.js 14, Tailwind CSS, shadcn/ui, React Flow, Recharts
- **Backend**: FastAPI, LangGraph, Pydantic v2
- **AI**: OpenRouter (Claude/GPT-4o/Gemini) or LM Studio (local Gemma)
- **Vector DB**: Qdrant
- **Database**: PostgreSQL (SQLAlchemy async)
- **Cache**: Redis
- **Deployment**: Vercel (frontend) + Railway (backend)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/athena-ai.git
cd athena-ai
```

### 2. Start Infrastructure
```bash
docker-compose up -d
```
This starts PostgreSQL, Qdrant, and Redis locally.

### 3. Start Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env        # Fill in your API keys
uvicorn main:app --reload --port 8000
```

### 4. Start Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/interview/start` | Start a new interview session |
| `POST` | `/api/v1/interview/respond` | Submit an answer, get next question |
| `GET`  | `/api/v1/interview/{id}/report` | Get the final structured report |
| `GET`  | `/api/v1/interview/{id}/status` | Get current interview status |
| `GET`  | `/health` | Health check |

### Start Interview — Request
```json
{
  "candidate_id": "cand_001",
  "name": "Aryan Shah",
  "completed_missions": [1, 2, 3, 5, 7],
  "skipped_topics": ["Quantization", "RLHF"],
  "curriculum_json": {}
}
```

### Respond — Request
```json
{
  "session_id": "sess_abc123",
  "answer": "RAG works by retrieving relevant chunks from a vector database..."
}
```

### Respond — Response
```json
{
  "session_id": "sess_abc123",
  "question_number": 3,
  "question": "How would you design a chunking strategy for legal documents?",
  "question_type": "architecture",
  "topic": "Chunking",
  "curriculum_day": 5,
  "reasoning_trace": {
    "weak_node": "Chunking",
    "dependency_path": ["Chunking", "Embeddings", "Vector DB", "RAG"],
    "human_explanation": "Your RAG answer was strong but skipped chunking strategy details."
  },
  "difficulty_level": 3,
  "interview_complete": false,
  "questions_remaining": 5
}
```

---

## 🤖 Multi-Agent Architecture

| Agent | Role |
|-------|------|
| Profile Analyzer | Reads candidate strengths/gaps from profile |
| Curriculum Planner | Plans which topics to cover next |
| Question Generator | Creates the actual question text |
| Reasoning Agent | Generates intelligent follow-up questions |
| Evaluation Agent | Scores answers across 6 dimensions |
| Learning Planner | Creates personalized 30/60/90-day roadmap |
| Chief Interview Agent | Synthesizes all agent opinions into final decision |
| Research/Coding/Architecture Agents | Specialist question proposers |

---

## 📋 Hackathon Requirements Checklist

- ✅ Conversational interview with context
- ✅ Minimum 8 questions
- ✅ Covers 4+ curriculum days
- ✅ Intelligent follow-up questions
- ✅ Structured feedback report
- ✅ Required HTTP endpoint
- ✅ Public GitHub repository
- ✅ Working live demo

---

## 📁 PROMPTS.md

See [PROMPTS.md](./PROMPTS.md) for the complete AI prompt history and usage log (required by hackathon).

---

## 📄 License

MIT License — see [LICENSE](./LICENSE)
