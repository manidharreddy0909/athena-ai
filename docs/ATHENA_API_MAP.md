# Athena AI API Map

## Base URL
`/api/v1`

## Endpoints

### 1. `POST /interview/start`
- **Description**: Initiates a new interview session.
- **Request Body**: `StartInterviewRequest`
  - `name` (str): Candidate name.
  - `completed_missions` (List[int]): Days completed in curriculum.
  - `skipped_topics` (List[str]): Topics the candidate skipped.
- **Response**: `StartInterviewResponse`
  - `session_id`, `question`, `topic`, `difficulty_level`, `reasoning_trace`.

### 2. `POST /interview/respond`
- **Description**: Submits the candidate's answer and processes the next state.
- **Request Body**: `RespondRequest`
  - `session_id` (str): The active session.
  - `answer` (str): Candidate's response.
- **Response**: `RespondResponse`
  - `question` (Next question), `answer_score`, `answer_feedback`, `interview_complete`, `reasoning_trace`.

### 3. `GET /interview/{session_id}/report`
- **Description**: Fetches the structured feedback report for a completed session.
- **Response**: `FeedbackReport`
  - Includes dimension scores, overall score, strong/weak areas, hiring recommendation, and knowledge graph snapshot.

### 4. `GET /interview/{session_id}/status`
- **Description**: Gets the current interview status without generating a full report.
- **Response**: Status JSON
  - `status`, `questions_asked`, `topics_covered`, `confidence_score`, `is_complete`.

## Internal Health
### `GET /` & `/docs`
- Root endpoint providing version and docs links. `/docs` provides Swagger UI.
