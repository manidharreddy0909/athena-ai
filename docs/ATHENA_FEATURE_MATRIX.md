# Athena AI Feature Matrix

## Core Capabilities
| Feature | Status | Description |
| :--- | :--- | :--- |
| **FastAPI Backend** | Verified | Robust backend serving API endpoints. |
| **Next.js Frontend** | Verified | Immersive UI with animations. |
| **LangGraph Orchestration** | Verified | State machine handling the interview loop. |
| **Adaptive Interview Flow** | Verified | Adjusts topics and difficulty dynamically. |
| **Question Generation** | Verified | Uses LLM to generate questions based on context. |
| **Answer Evaluation** | Verified | Evaluates user input for technical accuracy, clarity, and depth. |
| **Socratic Follow-ups** | Partial / Verified | `QuestionType.FOLLOW_UP` exists, relies on previous context. |
| **Final Report Generation** | Verified | Generates comprehensive feedback reports. |
| **Session Persistence** | Verified | Stores session state in LangGraph and local dicts (PostgreSQL via DB). |
| **Candidate State** | Verified | Uses Pydantic models to track candidate profiles and learning signals. |

## Advanced / Upgrades Planned
| Feature | Target Phase | Description |
| :--- | :--- | :--- |
| **Provider Abstraction** | Phase 3 | Abstract multiple LLMs (Gemini, Claude, OpenAI). |
| **BREATH Memory** | Phase 4 | Integration of robust semantic persistent memory. |
| **Universal Domain Engine** | Phase 6 | Expanding beyond CS/SWE topics. |
| **Voice Interviews** | Phase 7 | Speech-to-Text and Text-to-Speech integration. |
| **Multilingual Support** | Phase 8 | Support for English, Telugu, Hindi. |
| **Coding / System Design** | Phase 9 | Sandboxed code execution and whiteboard evaluation. |
| **Recruiter Mode** | Phase 11 | Dashboards, skill matrices, risk flags. |
| **RAG/Deep Research** | Phase 12 | Grounded answering using Qdrant vector store. |
| **Premium 3D UI** | Phase 15 | Enhanced UI/UX and optional 3D interviewer elements. |
