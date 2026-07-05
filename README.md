# Precedent

Institutional memory for on-call engineers.

Precedent is a Cognee-powered incident memory graph that catches recurring debugging loops before engineers waste another hour rediscovering the same root cause. Log a symptom and alert, and Precedent checks your team's own incident history for matching service failures, known root causes, and fixes.

## Why It Exists

On-call teams often solve the same class of incidents repeatedly:

- the Redis connection pool leaks again
- the payment retry loop double-charges customers again
- the auth service falls over because the old token path is still alive

Those lessons usually live in Slack threads, postmortems, ticket comments, or one engineer's memory. Precedent turns those lessons into an active memory system.

Instead of being a passive wiki, it interrupts the incident workflow:

> This looks familiar. You have seen this service fail this way before. Here are the previous root causes.

## Core Features

- **Precedent interrupt**: checks for similar incidents before saving a new one.
- **Incident timeline**: shows active service failures and lets engineers close the loop with a root cause.
- **Earned decommissioning**: moves fixed recurring patterns out of the active timeline.
- **Live memory graph**: visualizes services, incidents, symptoms, alerts, and root causes.
- **Clickable graph nodes**: click any node to inspect its description, metadata, and relationships.
- **Realtime updates**: timeline, resolved services, and graph views refresh automatically.
- **Safe seed flow**: deterministic demo data seeding that preserves data, removes duplicates, and avoids Groq rate-limit loops.

## Cognee Usage

Cognee is a required part of this project. Precedent uses Cognee as the semantic memory layer and graph-backed incident substrate.

| Cognee capability | Precedent behavior |
| --- | --- |
| `remember()` | Stores new incidents, root causes, and decommission markers into memory. |
| `recall()` / graph completion | Available for graph-based precedent search when enabled. |
| `improve()` | Supported for memory reinforcement, with safe timeout guards. |
| `forget()` | Supported behind an explicit opt-in flag to avoid accidental demo data loss. |
| Graph engine | Seed script builds a Cognee graph from local incident history. |

For realtime demo reliability, the default interrupt and graph endpoints use the active app-state projection while Cognee remains used for storage, seed graph construction, and optional recall.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python, Uvicorn |
| Memory | Cognee local mode or Cognee Cloud mode |
| App state | SQLite |
| Graph UI | Canvas force-directed graph |
| Deployment | Vercel frontend + Docker backend |

## Project Structure

```text
groundhog/
  backend/
    app/
      main.py                 FastAPI app and CORS setup
      cognee_client.py        Cognee integration and graph projection
      routes/
        entries.py            Incident create/list/root-cause routes
        interrupt.py          Precedent check route
        resolve.py            Decommission route
        graph.py              Memory graph route
      db/
        sqlite.py             SQLite persistence and active-state filters
        models.py             Pydantic API schemas
    seed/
      seed_data.py            Safe idempotent demo seeding
      local_graph_builder.py  Cognee graph builder without LLM-heavy extraction
    Dockerfile                Backend deploy image
  frontend/
    app/
      page.tsx                Incident reporting screen
      timeline/page.tsx       Active incident timeline
      resolved/page.tsx       Decommissioned precedent view
      memory/page.tsx         Memory graph page
      components/
        GraphView.tsx         Live clickable graph
        InterruptModal.tsx    Precedent interrupt modal
        EntryForm.tsx         Incident form
        PatternCard.tsx       Service precedent cards
    vercel.json               Vercel frontend config
  DEPLOYMENT.md               Deployment instructions
  PROJECT_REPORT.md           Full project report
```

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Cognee-compatible LLM configuration

### Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` with your provider keys. Do not commit `.env`.

Choose a Cognee memory mode:

**Local mode** stores Cognee memory on the backend host. Use this for local demos or a Docker backend with persistent disk:

```env
COGNEE_MODE=local
DATABASE_URL=sqlite:///./precedent.db
COGNEE_SKIP_CONNECTION_TEST=true
```

**Cloud mode** uses a hosted Cognee tenant. Use this when you do not want local graph/vector storage on the backend host:

```env
COGNEE_MODE=cloud
COGNEE_API_URL=https://your-cognee-tenant-url
COGNEE_API_TOKEN=your-cognee-api-token
DATABASE_URL=sqlite:///./precedent.db
```

In both modes, keep your LLM and embedding provider variables in `.env` or deployment platform secrets.

Seed the demo data:

```powershell
python -m seed.seed_data
```

Run the API:

```powershell
$env:PRECEDENT_RECALL_SOURCE="app_state"
$env:PRECEDENT_GRAPH_SOURCE="app_state"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

```powershell
cd frontend
npm install
$env:NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open:

```text
http://127.0.0.1:3000
```

## Demo Flow

1. Open the report screen.
2. Enter:
   - Symptom: `High latency on login`
   - Alert: `auth-service latency > 5s for /login`
   - Service: `auth-service`
3. The precedent modal appears with historical root causes.
4. Click **Apply Precedent** to avoid logging a duplicate investigation.
5. Go to **Incidents** and decommission a recurring service pattern.
6. Watch the active timeline and memory graph update automatically.
7. Click graph nodes to inspect descriptions and relationships.

## Deployment

Recommended deployment split:

- Frontend: Vercel
- Backend: Render, Railway, Fly.io, or any Docker host with persistent storage

See [DEPLOYMENT.md](DEPLOYMENT.md) for exact environment variables and commands.

## Important Safety Notes

- Do not commit `.env`, database files, Cognee system folders, or API keys.
- The seed script is idempotent and safe to rerun.
- Destructive Cognee reset/forget behavior is disabled by default and requires explicit environment flags.

## License

MIT
