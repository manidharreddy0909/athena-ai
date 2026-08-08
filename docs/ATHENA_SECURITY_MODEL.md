# Athena AI: Security Model

## Current State
- The backend is a standard FastAPI deployment without explicit JWT/OAuth authentication barriers on the primary endpoints, as it is a local/POC build.
- API keys are injected via local environment variables (or hardcoded in `config.py` for local dev instances like LM Studio).
- CORS is configured to accept requests strictly from `localhost:3000`.

## Planned Production Hardening
As per the Master Architecture mandate, the following vectors will be secured:

### 1. API Security
- **Authentication**: JWT validation for recruiter and candidate dashboards.
- **Authorization**: Role-Based Access Control (RBAC). Candidates cannot hit the `/report` endpoint.

### 2. AI Security (Prompt Protection)
- Implement safeguards against Prompt Injection and Data Exfiltration. The `evaluate_answer` module must sanitize input before submitting to the LLM.

### 3. Execution Security
- The planned **Coding Interview** functionality must run candidate code inside isolated Docker containers/sandboxes. Absolute prohibition against `eval()` or un-sandboxed shell execution on the host machine.

### 4. Secret Management
- Centralization of all API Keys (`GEMINI`, `BREATH`, `VOICE`) into a strictly ignored `.env` file. Keys will *never* be exposed to the React frontend client.
