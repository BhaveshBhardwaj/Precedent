"""Precedent — Institutional Memory for On-Call Engineers.

A knowledge graph powered by Cognee that catches you repeating your own
architectural mistakes, and lets you earn the right to forget them permanently.

FastAPI application with Cognee memory integration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import logging
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("groundhog")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup/shutdown lifecycle."""
    # ── Startup ──
    logger.info("🛡️ Precedent starting up...")

    # Initialize SQLite
    from app.db.sqlite import init_db
    await init_db()
    logger.info("SQLite database initialized")

    # Initialize Cognee
    from app.cognee_client import init_cognee
    await init_cognee()
    logger.info("Cognee memory system ready")

    yield

    # ── Shutdown ──
    logger.info("🛡️ Precedent shutting down...")


# Create the FastAPI app
app = FastAPI(
    title="Precedent",
    description=(
        "An institutional memory graph for on-call engineers. "
        "Before you investigate an alert, Precedent checks if this symptom "
        "has been solved before, surfacing historical root causes."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for Next.js frontend (port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount route modules
from app.routes import entries, interrupt, resolve, graph

app.include_router(entries.router)
app.include_router(interrupt.router)
app.include_router(resolve.router)
app.include_router(graph.router)


@app.get("/")
async def root():
    return {
        "app": "Precedent",
        "tagline": "Institutional Memory for On-Call",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
