# Athena AI: Memory Architecture

## Current State
The system currently utilizes a two-tier memory architecture designed for **Session Resilience**:

1. **In-Memory Volatile State**: The primary state of truth during an active interview loop. Stored in Python dictionaries keyed by `session_id`.
2. **SQLite Persistence Layer**: A background fallback database (`backend/db/`) that asynchronously syncs the in-memory state. If a commit fails (e.g., due to Windows file locks / WinError 1225), the orchestrator catches the error and continues the interview using the volatile memory.

## Planned Architecture: BREATH Persistent Memory Layer
The master evolution plan dictates the implementation of the **BREATH API**.

### Memory Categories (Planned)
- **Candidate Profile**: Extracted from resume/JD.
- **Short-Term Memory**: The active `InterviewState` (questions, answers, real-time scores).
- **Long-Term Consolidations**: Historical strengths, recurring mistakes across multiple interviews.

### Memory Controls
- Explicit commands to read, write, update, summarize, and expire candidate memories.
- Memories will be tagged with a `confidence` level and `provenance` timestamp to ensure the model does not hallucinate long-term state.
