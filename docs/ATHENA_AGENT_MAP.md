# Athena AI Agent Map

## Core Agents

Athena AI utilizes a multi-agent system decoupled from the main LangGraph state machine.

### 1. Profile Analyzer (`node_profile_analysis`)
- **Role**: Analyzes the initial candidate profile.
- **Responsibilities**:
  - Ingests `CandidateProfile` (completed days, skipped topics).
  - Configures the initial `KnowledgeGraph`.
  - Proposes the very first interview topic based on candidate weak spots or baseline requirements.
  - Generates the initial `ReasoningTrace`.

### 2. Question Agent (`generate_question`)
- **Role**: Content Generator.
- **Responsibilities**:
  - Generates specific question text based on instructions from the Chief Planner.
  - Adjusts tone and detail based on `DifficultyLevel` and `QuestionType`.
  - Injects recent conversational context and past answers to ensure conversational fluidity.

### 3. Evaluator Agent (`evaluate_answer`)
- **Role**: Scoring and Feedback.
- **Responsibilities**:
  - Reviews candidate's answer against the prompt.
  - Outputs a structured JSON assessment: `score` (0-1), `technical_accuracy`, `depth`, `clarity`, and concise `feedback`.
  - Determines `key_gaps` and `strong_points`.

### 4. Chief Interview Agent / Planner (`plan_next_question`)
- **Role**: Strategist.
- **Responsibilities**:
  - Observes the current state (questions asked, topics covered, mistake history).
  - Decides the `next_topic`, `question_type`, and `difficulty` for the upcoming turn.
  - Provides a `rationale` (ReasoningTrace) explaining *why* it chose this path (e.g., "Candidate failed DBMS last time, decreasing difficulty and probing normalization").

### 5. Report Agent (`generate_report` in `feedback_agent.py`)
- **Role**: Summarizer.
- **Responsibilities**:
  - Compiles the entire session history.
  - Generates the `FeedbackReport` with dimension scores (communication, coding, architecture), hiring recommendations, and customized 30/60/90 day learning plans.
