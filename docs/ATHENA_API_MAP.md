# Athena AI: API Map

## Base URL
`http://localhost:8000/api/v1`

## Interview Flow Endpoints

### 1. Start Interview
- **Route**: `POST /interview/start`
- **Description**: Initializes a new interview session and returns the first question.
- **Request**: `{ "name": "string", "completed_missions": [int], "skipped_topics": [string] }`
- **Response**: `session_id`, initial `question`, `topic`, `difficulty_level`.

### 2. Submit Answer
- **Route**: `POST /interview/respond`
- **Description**: Submits the candidate's answer for evaluation and returns the next question or completion signal.
- **Request**: `{ "session_id": "string", "answer": "string" }`
- **Response**: Evaluated `score`, `feedback`, next `question`, or `interview_complete: true`.

### 3. Fetch Report
- **Route**: `GET /interview/{session_id}/report`
- **Description**: Retrieves the finalized JSON feedback report for the recruiter dashboard.
- **Response**: Aggregated scores, hiring recommendation, strong/weak areas, and learning plan.

### 4. Fetch Status
- **Route**: `GET /interview/{session_id}/status`
- **Description**: Polls current state (questions asked, current topic, confidence score).
