# 🛡️ Precedent — Institutional Memory for On-Call Engineers

> Precedent is an institutional memory graph for on-call engineers. It catches you repeating the same architectural debugging loops — and lets you earn the right to forget them permanently.

## What it does

When a 3 AM incident hits, you log the symptom and the alert *before* you start debugging. Instead of just saving a ticket, Precedent searches the team's **own history** for the same symptom → alert → root cause loop, and — if it finds one — **interrupts you with the historical root causes** before you waste time reinventing the wheel.

*"You've seen this signature 4 times. Here's what the root cause was each time."*

This is not a generic wiki. This is **institutional memory used as a mirror**.

## Why Cognee

Precedent uses every stage of Cognee's memory lifecycle — not as decoration, but because each maps directly to a real DevOps need:

| Cognee Feature | Precedent Feature | Why |
|---|---|---|
| `remember()` with `node_set` | Store each incident with service scoping | Incidents need semantic structure (Symptoms vs Root Causes) |
| `recall()` with `GRAPH_COMPLETION` | **The Interrupt** — find past similar incidents via graph traversal | Embedding similarity alone misses the symptom→alert→fix *chain* |
| `improve()` | Pattern reinforcement | The more post-mortems logged, the tighter the graph |
| `forget()` | **Earned Forgetting** — decommission legacy services | Old alerts shouldn't pollute future context. You *earn* the right to prune the graph when you fix the architecture permanently. |
| Graph visualization | Live architecture graph | Watch your failure modes cluster and dissolve in real time |

The novel beat: **forgetting as a feature you earn, not a bug to prevent.**

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- An OpenAI API key (or any Cognee-supported LLM provider)

### Backend

```bash
cd groundhog/backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and add your LLM_API_KEY

# Seed demo data (optional but recommended for demos)
python -m seed.seed_data

# Start the server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd groundhog/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Open http://localhost:3000 — log an incident and watch the interrupt fire.

## Architecture

```
groundhog/
  backend/
    app/
      main.py              # FastAPI app with CORS + lifecycle
      cognee_client.py     # Cognee v1.0 API wrapper (remember/recall/improve/forget)
      routes/
        entries.py          # POST/GET incidents, PATCH root_cause
        interrupt.py        # POST /check-precedent (the interrupt)
        resolve.py          # POST /services/{id}/decommission (earned forgetting)
        graph.py            # GET /graph (live visualization data)
      db/
        sqlite.py           # App state: incidents, patterns
        models.py           # Pydantic schemas
    seed/
      seed_data.py          # 15 backdated incidents across 3 microservices
  frontend/
    app/
      page.tsx              # Log screen — "What broke this time?"
      timeline/page.tsx     # Incident history with post-mortem closing
      resolved/page.tsx     # Decommissioned Services (trophy room)
      components/
        InterruptModal.tsx   # THE demo hook — cinematic pattern interrupt
        EntryForm.tsx        # Incident logging form
        PatternCard.tsx      # Precedent display with counts
        GraphView.tsx        # Force-directed graph visualization
```

## Demo Script (90 seconds)

1. **0:00** — Open the app. Type Symptom: "High latency on login", Alert: "auth-service > 5s", Service: "auth-service"
2. **0:10** — 🚨 **InterruptModal fires**: "You've seen this signature 5 times. Here's what the root cause was each time (e.g. Redis connection leak)." ← *This is the aha moment*
3. **0:25** — Show the past instances with real root causes. Click "Apply Precedent".
4. **0:35** — Jump to Timeline, show the incident history.
5. **0:55** — Jump to Decommissioned Services. Explain how when you *finally* fix the architecture, you decommission the service.
6. **1:05** — Show the graph shrink in real time ← *forget() in action*
7. **1:20** — One-liner: "This is institutional memory used as a mirror. And forgetting a bad architecture is a feature you earn."

## Tech Stack

- **Backend**: Python 3.11, FastAPI, Cognee (embedded: SQLite + LanceDB + Kuzu)
- **Frontend**: Next.js 14 (App Router), TypeScript, TailwindCSS
- **Memory**: Cognee v1.0 API — the full lifecycle, not just store-and-retrieve

## License

MIT
