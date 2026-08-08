# Athena AI: System Architecture

## Overview
Athena AI is an autonomous, AI-driven technical interview platform. It currently supports a text-based interview flow designed to dynamically assess candidate knowledge, plan follow-up questions, and evaluate responses using an orchestrator powered by LangGraph.

## Component Stack
1. **Frontend**: Next.js 14+ (React), TailwindCSS, Framer Motion
   - Provides the `Start Interview` interface, real-time `Interview` loop, and the recruiter `Dashboard`.
2. **Backend**: FastAPI (Python 3.10+)
   - Handles the REST API endpoints and acts as the entry point for LangGraph orchestration.
3. **Orchestration**: LangGraph
   - Manages the state machine (StateGraph) for an interview session, handling loops between Question Generation, Answer Evaluation, and Planning.
4. **Database**: SQLite (SQLAlchemy + asyncpg support)
   - Stores session state and interview reports. Currently designed with an in-memory fallback strategy if DB transactions fail or lock.
5. **AI Integration**: OpenAI Compatible APIs (LM Studio/local models)
   - Uses a centralized `core.llm` provider wrapper that parses structured JSON out of unstructured plain text responses.

## Request Flow
1. **Candidate Profile Input**: User enters details on the frontend.
2. **Session Initialization (`/interview/start`)**: Backend creates a unique session ID, sets up a Digital Twin in memory, and triggers the first `Generate Question` node via LangGraph.
3. **Interview Loop (`/interview/respond`)**:
   - The user submits an answer.
   - LangGraph routes to the **Evaluate Answer** agent.
   - The **Chief Planner** agent determines the next topic and difficulty.
   - The **Question** agent generates the next prompt based on context.
4. **Completion (`/interview/report`)**: After `N` questions, the graph terminates, triggering the **Feedback Agent** to compile a final JSON-structured report.
