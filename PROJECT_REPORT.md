# Precedent Project Report

## Executive Summary

Precedent is an institutional memory system for on-call engineering teams. It helps engineers recognize recurring incidents before they repeat the same investigation. The app lets an engineer log a symptom, alert, and affected service, then checks previous incidents for matching root causes and fixes.

The key idea is simple: incident history should not be passive documentation. It should actively interrupt repeated failure loops.

Precedent combines:

- a FastAPI backend
- a Next.js frontend
- SQLite app state
- Cognee memory and graph capabilities
- a realtime incident and memory graph interface

## Problem Statement

On-call teams lose time because critical operational knowledge is fragmented across:

- Slack messages
- ticket comments
- postmortems
- dashboards
- individual memory

When the same service fails in a similar way, engineers often start from zero. Precedent turns those previous incidents into a searchable, graph-backed memory system.

## Product Concept

Precedent is built around three user actions:

1. **Report**: log a symptom, alert, service, and severity.
2. **Interrupt**: surface prior root causes before the new incident is saved.
3. **Decommission**: when the team permanently fixes a recurring pattern, remove it from the active workflow.

This creates a feedback loop:

```text
incident -> root cause -> precedent -> faster resolution -> decommissioned pattern
```

## User Experience

### Report View

The first screen is the actual workflow, not a landing page. Engineers enter the symptom and service. Precedent checks history before creating another incident.

### Precedent Modal

If prior history exists, a modal appears with:

- confidence level
- number of matching incidents
- previous symptoms and alerts
- root causes and fixes

The user can apply the precedent or log a new incident anyway.

### Timeline View

The timeline shows active incidents only. When a service pattern is decommissioned, incidents for that service leave the active timeline.

### Resolved View

Decommissioned patterns move into a resolved view. This gives the team a visible record of recurring issues that were handled permanently.

### Memory Graph

The memory graph shows:

- service nodes
- incident document nodes
- symptom nodes
- alert nodes
- root-cause/fix nodes
- relationships between them

The graph updates automatically and supports node click inspection. Clicking a node opens a details panel with metadata and connected relationships.

## Architecture

```text
Frontend (Next.js)
  |
  | HTTP/JSON
  v
Backend (FastAPI)
  |
  | app state
  v
SQLite
  |
  | semantic memory / graph construction
  v
Cognee
```

## Backend Design

The backend is a FastAPI application with route modules:

| Route file | Responsibility |
| --- | --- |
| `entries.py` | create incidents, list incidents, save root causes |
| `interrupt.py` | check for matching precedent |
| `resolve.py` | decommission service patterns |
| `graph.py` | return graph visualization data |

The backend keeps request paths fast by using SQLite for realtime app-state reads and background tasks for Cognee writes.

## Data Model

### Incidents

Each incident stores:

- `id`
- `user_id`
- `symptom`
- `alert`
- `service`
- `severity`
- `created_at`
- `root_cause_and_fix`
- `root_cause_logged_at`

### Patterns

Patterns represent recurring service-level incident clusters:

- `id`
- `user_id`
- `label`
- `service`
- `incident_count`
- `status`
- `streak_started_at`
- `decommissioned_at`

## Cognee Integration

Cognee is mandatory in Precedent. The project uses Cognee for memory lifecycle behavior and graph-backed context.

### Store

New incidents and root-cause updates are stored into Cognee with `remember()`. These writes run in background tasks so the UI does not block on LLM or graph latency.

### Recall

Cognee recall is supported for graph completion workflows. For the live demo, the default interrupt path uses active SQLite state to guarantee realtime behavior under API rate limits and graph DB locks.

### Improve

`improve()` is supported with timeout guards. It is not used in the default seed path because repeated LLM extraction can hit Groq token-per-minute limits.

### Forget

`forget()` is available behind an explicit environment flag. By default, decommissioning stores a Cognee resolution marker instead of deleting seed memory. This prevents accidental data loss during demos.

### Graph

The seed script builds a Cognee graph locally from incident history. The frontend graph endpoint uses active app-state projection by default so decommissioning updates the graph immediately.

## Realtime Behavior

The frontend polls every 2.5 seconds on:

- timeline
- resolved patterns
- memory graph

After decommission, the UI also applies an optimistic local update so the service disappears immediately from the active timeline.

## Safe Seeding

The seed process was redesigned because the original Cognee-heavy seed path could run for hours under Groq rate limits.

The current seed script:

- preserves existing seed data
- inserts only missing demo incidents
- inserts only missing service patterns
- removes duplicate incident and pattern rows
- avoids LLM-heavy extraction
- builds a Cognee graph from local SQLite records

This makes the seed command safe to rerun:

```powershell
python -m seed.seed_data
```

## Deployment Strategy

Precedent is split into two deployable services:

### Frontend

Deploy the `frontend/` directory to Vercel.

Set:

```bash
NEXT_PUBLIC_API_URL=https://your-backend-url
```

### Backend

Deploy `backend/` as a Docker web service on a stateful host such as Render, Railway, Fly.io, or a VM.

The backend needs persistent storage for SQLite and Cognee local files. Vercel serverless functions are not a good fit for the backend because local state is ephemeral.

## Demo Script

1. Open the app.
2. Report an incident:
   - Symptom: `High latency on login`
   - Alert: `auth-service latency > 5s for /login`
   - Service: `auth-service`
3. Show the precedent interrupt.
4. Apply the precedent.
5. Open the incident timeline.
6. Decommission a recurring pattern.
7. Show that active incidents and graph nodes update.
8. Click a graph node to inspect its description and relationships.

## Current Status

Implemented:

- incident reporting
- precedent checking
- root-cause logging
- decommissioning
- duplicate-safe seed script
- realtime timeline and graph refresh
- clickable graph node details
- frontend Vercel config
- backend Dockerfile
- deployment documentation

## Known Tradeoffs

- SQLite is appropriate for the demo and small teams, but a production deployment should use Postgres.
- The frontend currently uses polling instead of WebSockets or Server-Sent Events.
- Cognee recall is available but not the default realtime interrupt path because provider rate limits and local graph locks can slow request/response UX.
- Authentication is not implemented; this is a hackathon/demo scope app.

## Conclusion

Precedent demonstrates how an incident memory system can become active operational infrastructure. It does not just store postmortems. It uses prior incidents to interrupt repeated debugging loops, guide engineers toward known fixes, and mark recurring service failures as resolved when the architecture improves.
