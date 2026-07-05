"""Decommission route — POST /services/{id}/decommission.

This is the novel beat: forget() as a user-facing feature.
When a service gets decommissioned, you forget() everything tied to it —
a real, defensible reason to prune a graph.
"""

from fastapi import APIRouter, HTTPException
from app.db.models import IncidentPatternResponse
from app.db import sqlite
from app.cognee_client import decommission_and_forget

router = APIRouter(tags=["services"])


@router.post("/services/{pattern_id}/decommission", response_model=IncidentPatternResponse)
async def decommission_service(pattern_id: str):
    """Decommission a service — the user has earned the right to forget.

    1. Marks the pattern as 'decommissioned' in SQLite
    2. Calls Cognee forget() to clear the semantic memory
    3. The service moves from Timeline to Decommissioned Services
    """
    pattern = await sqlite.get_pattern(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Service/Pattern not found")

    if pattern["status"] == "decommissioned":
        raise HTTPException(status_code=400, detail="Service already decommissioned")

    # Call Cognee forget() — even if this fails, the SQLite update drives the UI
    await decommission_and_forget(
        user_id=pattern["user_id"],
        service=pattern["service"],
        pattern_id=pattern_id,
    )

    # Update SQLite status
    result = await sqlite.decommission_service(pattern_id)

    return IncidentPatternResponse(**result)


@router.get("/services", response_model=list[IncidentPatternResponse])
async def list_services(status: str = None):
    """Get all patterns, optionally filtered by status ('active' or 'decommissioned')."""
    patterns = await sqlite.get_patterns(status=status)
    return [IncidentPatternResponse(**p) for p in patterns]


@router.get("/services/{pattern_id}", response_model=IncidentPatternResponse)
async def get_service(pattern_id: str):
    """Get a single service pattern by ID."""
    pattern = await sqlite.get_pattern(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Service pattern not found")
    return IncidentPatternResponse(**pattern)
