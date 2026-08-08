# Athena AI Memory Architecture

Athena AI employs a robust 4-layer persistent memory engine (`memory/memory_engine.py`) to manage context and intelligence.

## Layer 1: Short-Term Memory
- **Implementation**: In-memory list (`ShortTermMemory`).
- **Function**: Stores the last N Q&A pairs.
- **Usage**: Prepended directly into LLM prompts as conversational context to maintain contextual continuity and enable follow-ups without blowing up the context window.

## Layer 2: Semantic Memory
- **Implementation**: Qdrant Vector Store (Planned / Configured via `config.py`).
- **Function**: Stores broad conceptual knowledge, past session data, or RAG documents.
- **Usage**: Used to retrieve relevant grounded context when asking deep technical questions or checking if an answer aligns with standard documentation.

## Layer 3: Interview Memory
- **Implementation**: Structured state (tracked in `InterviewMemory`, persisted in PostgreSQL).
- **Function**: Tracks explicit metadata: topics covered, curriculum days, counts of mistakes, and strong answers.
- **Usage**: Helps the Chief Planner enforce rules like "cover at least 4 curriculum days" and "avoid repeating recently asked topics."

## Layer 4: Reasoning Memory
- **Implementation**: JSON blobs/Trace logs (`ReasoningMemory`).
- **Function**: Stores the internal debate logs, rationales, and "Why did I ask this?" explanations for every single question.
- **Usage**: Feeds the Explainable AI UI panel for candidates, and provides deep insights for recruiter dashboards.

## BREATH Integration (Phase 4)
- **Goal**: Abstract `MemoryEngine` over the `BREATH` persistent memory API layer for cross-session long-term memory. This will allow Athena to remember candidate weaknesses across multiple interviews separated by months.
