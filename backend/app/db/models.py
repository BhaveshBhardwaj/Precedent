"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


def generate_id() -> str:
    return str(uuid.uuid4())


# ── Incident models ────────────────────────────────────────────────────────────

class IncidentCreate(BaseModel):
    symptom: str = Field(..., description="What is the symptom or error signature (e.g., 'high memory usage, pod crashing')")
    alert: str = Field(..., description="The alert that fired (e.g., 'CPU > 90% on auth service')")
    service: str = Field(..., description="The affected service (e.g., 'Auth', 'Payments')")
    severity: Optional[str] = Field(None, description="Severity level")


class RootCauseUpdate(BaseModel):
    root_cause_and_fix: str = Field(..., description="What was the root cause and how was it fixed (e.g., 'connection pool exhaustion after a deploy, bumped max connections')")


class IncidentResponse(BaseModel):
    id: str
    user_id: str
    symptom: str
    alert: str
    service: str
    severity: Optional[str]
    created_at: str
    root_cause_and_fix: Optional[str]
    root_cause_logged_at: Optional[str]


# ── Pattern models ──────────────────────────────────────────────────────────

class IncidentPatternResponse(BaseModel):
    id: str
    user_id: str
    label: str
    service: str
    incident_count: int
    status: str  # "active" | "decommissioned"
    streak_started_at: Optional[str]
    decommissioned_at: Optional[str]


class DecommissionServiceRequest(BaseModel):
    label: Optional[str] = None  # Optional note for decommission


# ── Precedent / check-precedent models ────────────────────────────────────────

class CheckPrecedentRequest(BaseModel):
    symptom: str
    alert: str
    service: str


class PastIncident(BaseModel):
    date: str
    symptom: str
    alert: str
    root_cause_and_fix: Optional[str]


class PrecedentResponse(BaseModel):
    precedent_found: bool
    match_count: int
    confidence: str  # "none" | "emerging" | "recurring" | "deep_loop"
    past_incidents: List[str]  # Raw recall results from Cognee
    message: str


# ── Graph models ────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    label: str
    type: Optional[str] = None
    properties: dict = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str
    properties: dict = {}


class GraphResponse(BaseModel):
    nodes: List[dict]
    edges: List[dict]

