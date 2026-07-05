# Deployment

Precedent has two deployable parts:

- `backend/`: FastAPI + SQLite + Cognee integration. This should run as a stateful web service with a persistent disk.
- `frontend/`: Next.js app. This can run on Vercel and point at the backend URL.

## Recommended Setup

### 1. Backend on Render, Railway, Fly, or any Docker host

Use `backend/Dockerfile` as the service image.

Required environment variables:

```bash
DATABASE_URL=sqlite:////data/precedent.db
PRECEDENT_RECALL_SOURCE=app_state
PRECEDENT_GRAPH_SOURCE=app_state
COGNEE_RECALL_TIMEOUT_SECONDS=3
COGNEE_WRITE_TIMEOUT_SECONDS=8
LLM_API_KEY=...
GROQ_API_KEY=...
LLM_PROVIDER=openai
LLM_MODEL=groq/llama-3.1-8b-instant
EMBEDDING_PROVIDER=fastembed
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSIONS=384
COGNEE_MODE=local
COGNEE_SKIP_CONNECTION_TEST=true
```

Mount a persistent disk at `/data` so `precedent.db` survives restarts.

The container starts by running:

```bash
python -m seed.seed_data
```

That seed path is idempotent: it keeps existing seed data, removes duplicates, and avoids Groq-heavy Cognee extraction.

### 2. Frontend on Vercel

Create a Vercel project with root directory:

```bash
frontend
```

Set this environment variable in Vercel:

```bash
NEXT_PUBLIC_API_URL=https://your-backend-url
```

Then deploy the frontend.

## Why Not Backend-Only Vercel?

The backend uses SQLite and local Cognee state. Vercel serverless functions are not a good fit for this because local filesystem state is ephemeral and long-lived Cognee graph/vector workers can be interrupted.

Use Vercel for the Next.js frontend and a stateful Docker host for the backend.
