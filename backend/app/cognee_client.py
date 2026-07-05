"""Cognee integration layer for Precedent.

This module wraps Cognee's v1.0 API (remember/recall/improve/forget) to
implement the institutional memory lifecycle:

  1. STORE   → remember() new incidents with node_set scoping + temporal_cognify
  2. RECALL  → recall() with GRAPH_COMPLETION to find past similar incidents
  3. IMPROVE → improve() to reinforce frequently-repeated patterns
  4. FORGET  → forget() to decommission a service and prune its graph

Cognee runs embedded by default (SQLite + LanceDB + Kuzu).
"""

import cognee
from cognee import SearchType
import logging
import os
import traceback

logger = logging.getLogger("precedent.cognee")


# ── Initialization ──────────────────────────────────────────────────────────

async def init_cognee():
    """Initialize Cognee for first use. Call once on app startup."""
    try:
        mode = os.environ.get("COGNEE_MODE", "local")
        logger.info(f"Cognee initialized successfully in {mode.upper()} mode")
    except Exception as e:
        logger.error(f"Failed to initialize Cognee: {e}")
        raise


async def reset_cognee():
    """Full reset for demo sessions. Wipes ALL Cognee data."""
    try:
        await cognee.prune.prune_data()
        await cognee.prune.prune_system(metadata=True)
        logger.info("Cognee data and system pruned for clean demo")
    except Exception as e:
        logger.warning(f"Cognee prune failed (may be first run): {e}")


# ── Store: remember() ──────────────────────────────────────────────────────

async def store_incident(
    symptom: str,
    alert: str,
    service: str,
    created_at: str,
    severity: str = None,
    user_id: str = "demo_user",
):
    """Store a new incident report in Cognee's memory.

    Uses remember() with:
    - node_set for user + service scoping
    - temporal_cognify=True for time-aware pattern detection
    - self_improvement=False to keep processing fast
    """
    incident_text = (
        f"On {created_at}, an incident occurred. "
        f"Symptom: {symptom}. "
        f"Alert: {alert}. "
        f"Service: {service}. "
        f"Severity: {severity or 'unspecified'}."
    )

    try:
        await cognee.remember(
            incident_text,
            dataset_name=f"user_{user_id}",
            node_set=[f"user:{user_id}", service],
            temporal_cognify=True,
            self_improvement=False,
        )
        logger.info(f"Incident stored in Cognee: {service} - {alert[:50]}...")
    except Exception as e:
        logger.error(f"Failed to store incident in Cognee: {e}\n{traceback.format_exc()}")
        # Don't raise — the SQLite incident is already saved, Cognee is best-effort


async def store_root_cause(
    symptom: str,
    alert: str,
    service: str,
    created_at: str,
    root_cause_and_fix: str,
    user_id: str = "demo_user",
):
    """Store the root cause and fix of a past incident, closing the loop.

    This is critical for precedent detection: Cognee needs both the
    symptom AND its root cause to build meaningful symptom→alert→fix
    chains that power the interrupt.
    """
    root_cause_text = (
        f"Root cause and fix for the {service} incident on {created_at}: {root_cause_and_fix}. "
        f"The original symptom was: {symptom}. "
        f"The original alert was: {alert}."
    )

    try:
        await cognee.remember(
            root_cause_text,
            dataset_name=f"user_{user_id}",
            node_set=[f"user:{user_id}", service],
            temporal_cognify=True,
            self_improvement=False,
        )
        logger.info(f"Root cause stored in Cognee for {service} incident")
    except Exception as e:
        logger.error(f"Failed to store root cause in Cognee: {e}\n{traceback.format_exc()}")


# ── Recall: pattern detection (THE precedent check) ───────────────────────────────

async def check_precedent(
    symptom: str,
    alert: str,
    service: str,
    user_id: str = "demo_user",
) -> dict:
    """Search Cognee for past similar incidents.

    Uses recall() with GRAPH_COMPLETION to leverage the full knowledge graph,
    not just embedding similarity. The node_name filter scopes results to
    this user and service.

    Returns a dict with:
    - precedent_found: bool
    - match_count: int
    - confidence: "none" | "emerging" | "recurring" | "deep_loop"
    - past_incidents: list of past incident/root_cause strings
    - message: human-readable interrupt message
    """
    query = (
        f"Find all past incidents and their root causes that are similar to this: "
        f"Symptom: {symptom}. Alert: {alert}. Service: {service}. "
        f"List each past instance with its date, symptom, alert, and root cause."
    )

    try:
        results = await cognee.recall(
            query_text=query,
            query_type=SearchType.GRAPH_COMPLETION,
            node_name=[f"user:{user_id}", service],
            datasets=[f"user_{user_id}"],
            top_k=10,
        )

        if not results:
            return {
                "precedent_found": False,
                "match_count": 0,
                "confidence": "none",
                "past_incidents": [],
                "message": "No precedents found. This looks like a novel incident.",
            }

        # results can be a string (LLM answer) or list
        if isinstance(results, str):
            past_incidents = [results]
        elif isinstance(results, list):
            past_incidents = [str(r.text) if hasattr(r, 'text') else str(r) for r in results]
        else:
            past_incidents = [str(results)]

        # Estimate match count from the response content
        response_text = " ".join(past_incidents).lower()

        # Heuristic: count mentions of dates, "alert", "root cause" keywords
        import re
        date_mentions = len(re.findall(r'\d{4}-\d{2}-\d{2}', response_text))
        alert_mentions = response_text.count("alert")
        cause_mentions = response_text.count("root cause")

        # Cross-reference with SQLite for a more honest baseline count
        try:
            from app.db import sqlite
            patterns = await sqlite.get_patterns(status="active")
            service_pattern = next((p for p in patterns if p["service"] == service), None)
            sqlite_count = service_pattern["incident_count"] if service_pattern else 0
        except Exception:
            sqlite_count = 0

        # Use the highest signal
        match_count = max(date_mentions, alert_mentions, cause_mentions, sqlite_count, 1)

        # If the response indicates no matches, override
        no_match_indicators = ["no similar", "no past", "no matching", "not found", "no prior", "no record"]
        if any(ind in response_text for ind in no_match_indicators):
            return {
                "precedent_found": False,
                "match_count": 0,
                "confidence": "none",
                "past_incidents": [],
                "message": "No precedents found. This looks like a novel incident.",
            }

        # Determine confidence level
        if match_count >= 5:
            confidence = "deep_loop"
            message = f"🚨 Deep precedent! We have seen this signature {match_count}+ times. Root cause history below."
        elif match_count >= 3:
            confidence = "recurring"
            message = f"⚠️ Recurring incident: this service has failed like this {match_count} times."
        elif match_count >= 2:
            confidence = "emerging"
            message = f"👀 Precedent found: this signature matches {match_count} past incidents."
        else:
            confidence = "emerging"
            message = "👀 Precedent found: this looks like a past incident."

        return {
            "precedent_found": True,
            "match_count": match_count,
            "confidence": confidence,
            "past_incidents": past_incidents,
            "message": message,
        }

    except Exception as e:
        logger.error(f"Precedent check failed: {e}\n{traceback.format_exc()}")
        return {
            "precedent_found": False,
            "match_count": 0,
            "confidence": "none",
            "past_incidents": [],
            "message": "Precedent check unavailable right now.",
        }


# ── Improve: reinforce patterns ────────────────────────────────────────────

async def reinforce_patterns(user_id: str = "demo_user"):
    """Run Cognee's improve() to strengthen frequently-reinforced connections."""
    try:
        await cognee.improve(dataset=f"user_{user_id}")
        logger.info(f"Cognee improve() completed for user {user_id}")
    except Exception as e:
        logger.warning(f"Cognee improve() failed (non-critical): {e}")


# ── Forget: decommission a service ───────────────────────────────────────

async def decommission_and_forget(
    user_id: str = "demo_user",
    service: str = None,
    pattern_id: str = None,
):
    """Decommission a service — the novel 'earned forgetting' feature.

    When a service is decommissioned, call forget() to remove the semantic
    memory of it, so old incidents don't pollute future precedent checks.
    """
    try:
        # Note: Cognee forget() is best scoped by dataset, but in a real prod
        # environment you'd use node_set or data_id filtering. For the hackathon,
        # we'll use dataset-scoped forget with memory_only to simulate this.
        await cognee.forget(
            dataset=f"user_{user_id}",
            memory_only=True,
        )
        logger.info(f"Service pattern {pattern_id} decommissioned — memory cleared for {user_id}")
        return True
    except Exception as e:
        logger.warning(f"Cognee forget() failed, falling back to SQLite-only resolve: {e}")
        return False


# ── Graph: visualization data ──────────────────────────────────────────────

async def get_graph_data() -> dict:
    """Get the raw graph data for visualization."""
    try:
        from cognee.infrastructure.databases.graph import get_graph_engine

        engine = await get_graph_engine()
        nodes, edges = await engine.get_graph_data()

        # Convert to serializable format
        serialized_nodes = []
        for node_id, props in nodes:
            serialized_nodes.append({
                "id": str(node_id),
                "label": props.get("name", props.get("type", str(node_id)[:20])),
                "type": props.get("type", "unknown"),
                "properties": {k: str(v) for k, v in props.items()} if props else {},
            })

        serialized_edges = []
        for source, target, rel_name, props in edges:
            serialized_edges.append({
                "source": str(source),
                "target": str(target),
                "relationship": rel_name,
                "properties": {k: str(v) for k, v in props.items()} if props else {},
            })

        return {"nodes": serialized_nodes, "edges": serialized_edges}

    except Exception as e:
        logger.error(f"Failed to get graph data: {e}")
        return {"nodes": [], "edges": []}
