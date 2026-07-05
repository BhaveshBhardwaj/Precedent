"""Incident routes — POST/GET /incidents, PATCH /incidents/{id}/root_cause."""

from fastapi import APIRouter, HTTPException
from app.db.models import IncidentCreate, IncidentResponse, RootCauseUpdate
from app.db import sqlite
from app.cognee_client import store_incident, store_root_cause, reinforce_patterns
import uuid

router = APIRouter(tags=["incidents"])


@router.post("/incidents", response_model=IncidentResponse)
async def create_incident(incident: IncidentCreate):
    """Log a new incident report.

    Saves to SQLite for fast UI reads, then asynchronously stores in Cognee
    for semantic memory. Also triggers pattern reinforcement every 5 incidents.
    """
    incident_id = str(uuid.uuid4())

    # Save to SQLite (fast, for UI)
    result = await sqlite.create_incident(
        id=incident_id,
        symptom=incident.symptom,
        alert=incident.alert,
        service=incident.service,
        severity=incident.severity,
    )

    # Check if a pattern for this service exists
    patterns = await sqlite.get_patterns(status="active")
    service_pattern = next((p for p in patterns if p["service"] == incident.service), None)

    if service_pattern:
        await sqlite.increment_pattern_count(service_pattern["id"])
    else:
        pattern_id = str(uuid.uuid4())
        await sqlite.create_pattern(
            id=pattern_id,
            label=f"{incident.service} Precedents",
            service=incident.service,
            incident_count=1,
            status="active"
        )

    # Store in Cognee (semantic memory — may take a moment)
    try:
        await store_incident(
            symptom=incident.symptom,
            alert=incident.alert,
            service=incident.service,
            created_at=result["created_at"],
            severity=incident.severity,
        )
    except Exception:
        pass  # Cognee storage is best-effort; SQLite incident is already saved

    # Reinforce patterns every 5 incidents
    try:
        count = await sqlite.get_incident_count()
        if count % 5 == 0 and count > 0:
            await reinforce_patterns()
    except Exception:
        pass  # Non-critical

    return IncidentResponse(**result)


@router.get("/incidents", response_model=list[IncidentResponse])
async def list_incidents():
    """Get all incidents for the demo user, newest first."""
    incidents = await sqlite.get_incidents()
    return [IncidentResponse(**i) for i in incidents]


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str):
    """Get a single incident by ID."""
    incident = await sqlite.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentResponse(**incident)


@router.patch("/incidents/{incident_id}/root_cause", response_model=IncidentResponse)
async def update_root_cause(incident_id: str, body: RootCauseUpdate):
    """Close the loop: record the root cause and fix of a past incident.

    This is critical for precedent detection — Cognee needs both the
    symptom AND its root cause to surface meaningful precedents.
    """
    # Get the original incident first
    incident = await sqlite.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Update SQLite
    result = await sqlite.update_root_cause(incident_id, body.root_cause_and_fix)

    # Store outcome in Cognee
    try:
        await store_root_cause(
            symptom=incident["symptom"],
            alert=incident["alert"],
            service=incident["service"],
            created_at=incident["created_at"],
            root_cause_and_fix=body.root_cause_and_fix,
        )
    except Exception:
        pass  # Best-effort

    return IncidentResponse(**result)

