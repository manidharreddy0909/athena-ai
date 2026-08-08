# Athena AI Architecture

## Overview
Athena AI is an autonomous interview intelligence platform. It orchestrates a multi-agent debate to simulate dynamic, Socratic interview sessions. The application is built using a modern decoupled architecture consisting of a Python/FastAPI backend and a Next.js/React frontend.

## Core Stack
- **Frontend**: Next.js 14 (App Router), React 19, TailwindCSS, Framer Motion for UI animations, Recharts for analytics.
- **Backend**: FastAPI, Uvicorn, Pydantic for data validation and typing.
- **Orchestration**: LangGraph and LangChain for stateful agent workflows.
- **LLM Integration**: OpenAI-compatible client, structured to support LM Studio, OpenRouter, Groq, and direct provider APIs (Gemini, Claude).
- **Database**: PostgreSQL (via asyncpg and SQLAlchemy) for structured state.
- **Vector Search**: Qdrant for semantic search and retrieval.
- **Cache / Message Queue**: Redis.

## System Components

### 1. Frontend Client
- **Home / Landing (`/app/page.tsx`)**: Collects initial candidate profile, handles interview initiation.
- **Interview Interface (`/app/interview/page.tsx`)**: Real-time Q&A interface. Supports conversational interactions, explainable AI display (showing agent reasoning), and session progress tracking.

### 2. API Gateway (FastAPI)
- Exposes RESTful endpoints in `/api/v1/interview`.
- Endpoints manage session lifecycle: `/start`, `/respond`, `/report`, `/status`.
- Handles CORS, configuration validation, and request parsing.

### 3. State Machine Orchestration (LangGraph)
- `graph/orchestrator.py` defines the state machine governing the interview loop.
- **State Flow**: `INIT → PROFILE_ANALYSIS → QUESTION → ANSWER → EVALUATION → MEMORY_UPDATE → NEXT_QUESTION → REPORT`.
- Manages the `InterviewState` containing session details, agent trace, and candidate history.

### 4. Multi-Agent System
- Uses specialized functional agents decoupled from the main execution flow.
- **Profile Analyzer**: Establishes initial learning focus and configures the Knowledge Graph.
- **Question Agent**: Synthesizes context to generate focused, domain-specific questions.
- **Evaluator Agent**: Scores answers on technical accuracy, depth, and clarity.
- **Chief Interview Agent (Planner)**: Analyzes weak/strong topics, controls difficulty mapping, and decides the next question type based on historical context.

### 5. Persistent Memory Architecture
- A 4-layer engine (`memory/memory_engine.py`):
  1. **Short-Term Memory**: In-memory list (recent Q&A pairs for direct LLM injection).
  2. **Semantic Memory**: Qdrant-backed vector search for broad conceptual retrieval.
  3. **Interview Memory**: PostgreSQL structural state (topics covered, days, mistakes).
  4. **Reasoning Memory**: Trace blobs for agent debate logs (used in Explainable AI).

## Request Flow Example
1. User provides profile data and initiates interview on Frontend.
2. `POST /api/v1/interview/start` is hit. FastAPI validates via Pydantic (`StartInterviewRequest`).
3. LangGraph initiates `node_profile_analysis` configuring the Knowledge Graph and determining the first topic.
4. `node_generate_question` interacts with LLM to generate the first question text.
5. Response is passed to Frontend. User inputs an answer.
6. `POST /api/v1/interview/respond` triggers LangGraph to resume.
7. Evaluator Agent scores answer -> Memory Engine updates -> Chief Planner determines next step -> next Question generated.
