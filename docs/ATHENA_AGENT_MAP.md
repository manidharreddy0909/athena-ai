# Athena AI: Agent Map

## Orchestration (LangGraph)
The core interview loop is a deterministic state machine powered by `langgraph`.

## Specialized Agents

### 1. `generate_question` (Question Agent)
- **Role**: Takes the planned topic, difficulty, and type, and generates the exact wording of the interview question.
- **Node Name**: `generate_question`

### 2. `evaluate_answer` (Evaluator Agent)
- **Role**: Evaluates the candidate's answer against the active question. Computes a score (0.0 - 1.0) and generates concise feedback. Handles fallback routing if LLM parsing fails.
- **Node Name**: `evaluate_answer`

### 3. `plan_next` (Chief Planner Agent)
- **Role**: Analyzes the candidate's history, weak spots, and current curriculum coverage to determine the *next* topic and optimal difficulty level.
- **Node Name**: `plan_next`

### 4. `generate_report` (Feedback Agent)
- **Role**: Summarizes the entire `qa_history` at the end of the interview. Determines final hiring recommendation and outputs actionable learning pathways.

## Graph Execution Flow
```text
START -> [profile_analysis] -> [generate_question] 
                                    v (Wait for Answer)
         [plan_next] <- [memory_update] <- [evaluate_answer]
              |
              +-> (Loop back to generate_question)
              |
         (Complete) -> [generate_report] -> END
```
