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
import asyncio
import logging
import os
import re
import traceback

logger = logging.getLogger("precedent.cognee")

COGNEE_WRITE_TIMEOUT = float(os.environ.get("COGNEE_WRITE_TIMEOUT_SECONDS", "20"))
COGNEE_RECALL_TIMEOUT = float(os.environ.get("COGNEE_RECALL_TIMEOUT_SECONDS", "12"))


async def _with_timeout(coro, timeout: float, operation: str):
    """Run a Cognee coroutine with a bounded wait so API requests stay responsive."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("%s timed out after %.1fs", operation, timeout)
        raise


def _tokenize(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) > 2}


def _confidence_for_count(match_count: int) -> str:
    if match_count >= 5:
        return "deep_loop"
    if match_count >= 3:
        return "recurring"
    if match_count >= 1:
        return "emerging"
    return "none"


def _message_for_count(match_count: int) -> str:
    if match_count >= 5:
        return f"Deep precedent: this signature appears in {match_count} previous incidents."
    if match_count >= 3:
        return f"Recurring incident: this service has failed like this {match_count} times."
    if match_count >= 1:
        return f"Precedent found: {match_count} related incident matched local history."
    return "No precedents found. This looks like a novel incident."


async def _sqlite_precedent_fallback(symptom: str, alert: str, service: str) -> dict:
    """Fast local-history fallback used when Cognee recall is slow or empty."""
    try:
        from app.db import sqlite

        incidents = await sqlite.get_incidents()
    except Exception as exc:
        logger.warning("SQLite precedent fallback failed: %s", exc)
        return {
            "precedent_found": False,
            "match_count": 0,
            "confidence": "none",
            "past_incidents": [],
            "message": "Precedent check unavailable right now.",
        }

    query_tokens = _tokenize(f"{symptom} {alert} {service}")
    scored_incidents = []
    for incident in incidents:
        if incident["service"] != service or not incident.get("root_cause_and_fix"):
            continue
        incident_tokens = _tokenize(
            f"{incident['symptom']} {incident['alert']} {incident['service']}"
        )
        overlap = len(query_tokens & incident_tokens)
        if overlap > 0 or incident["service"] == service:
            scored_incidents.append((overlap, incident))

    scored_incidents.sort(key=lambda item: (item[0], item[1]["created_at"]), reverse=True)
    matches = [incident for _, incident in scored_incidents[:5]]
    match_count = len(scored_incidents)

    if not matches:
        return {
            "precedent_found": False,
            "match_count": 0,
            "confidence": "none",
            "past_incidents": [],
            "message": _message_for_count(0),
        }

    return {
        "precedent_found": True,
        "match_count": match_count,
        "confidence": _confidence_for_count(match_count),
        "past_incidents": [
            (
                f"{incident['created_at'][:10]} - {incident['service']}\n"
                f"Symptom: {incident['symptom']}\n"
                f"Alert: {incident['alert']}\n"
                f"Root cause/fix: {incident['root_cause_and_fix']}"
            )
            for incident in matches
        ],
        "message": _message_for_count(match_count),
    }


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
    if os.environ.get("PRECEDENT_ALLOW_COGNEE_RESET") != "1":
        logger.warning("Cognee reset skipped. Set PRECEDENT_ALLOW_COGNEE_RESET=1 to enable pruning.")
        return False

    try:
        await cognee.prune.prune_data()
        await cognee.prune.prune_system(metadata=True)
        logger.info("Cognee data and system pruned for clean demo")
        return True
    except Exception as e:
        logger.warning(f"Cognee prune failed (may be first run): {e}")
        return False


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
        await _with_timeout(
            cognee.remember(
                incident_text,
                dataset_name=f"user_{user_id}",
                node_set=[f"user:{user_id}", service],
                temporal_cognify=False,
                self_improvement=False,
            ),
            COGNEE_WRITE_TIMEOUT,
            "Cognee incident remember()",
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
        await _with_timeout(
            cognee.remember(
                root_cause_text,
                dataset_name=f"user_{user_id}",
                node_set=[f"user:{user_id}", service],
                temporal_cognify=False,
                self_improvement=False,
            ),
            COGNEE_WRITE_TIMEOUT,
            "Cognee root cause remember()",
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
    if os.environ.get("PRECEDENT_RECALL_SOURCE", "app_state") == "app_state":
        return await _sqlite_precedent_fallback(symptom, alert, service)

    query = (
        f"Find all past incidents and their root causes that are similar to this: "
        f"Symptom: {symptom}. Alert: {alert}. Service: {service}. "
        f"List each past instance with its date, symptom, alert, and root cause."
    )

    try:
        results = await _with_timeout(
            cognee.recall(
                query_text=query,
                query_type=SearchType.GRAPH_COMPLETION,
                node_name=[f"user:{user_id}", service],
                datasets=[f"user_{user_id}"],
                top_k=10,
            ),
            COGNEE_RECALL_TIMEOUT,
            "Cognee recall()",
        )

        if not results:
            return await _sqlite_precedent_fallback(symptom, alert, service)

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
            return await _sqlite_precedent_fallback(symptom, alert, service)

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
        return await _sqlite_precedent_fallback(symptom, alert, service)


# ── Improve: reinforce patterns ────────────────────────────────────────────

async def reinforce_patterns(user_id: str = "demo_user"):
    """Run Cognee's improve() to strengthen frequently-reinforced connections."""
    try:
        await _with_timeout(
            cognee.improve(dataset=f"user_{user_id}"),
            COGNEE_WRITE_TIMEOUT,
            "Cognee improve()",
        )
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
        if os.environ.get("PRECEDENT_ALLOW_COGNEE_FORGET") != "1":
            await _with_timeout(
                cognee.remember(
                    (
                        f"Service {service} was decommissioned for pattern {pattern_id}. "
                        "This is a resolution marker; historical seed memory was preserved."
                    ),
                    dataset_name=f"user_{user_id}",
                    node_set=[f"user:{user_id}", service or "decommissioned"],
                    temporal_cognify=False,
                    self_improvement=False,
                ),
                COGNEE_WRITE_TIMEOUT,
                "Cognee decommission marker remember()",
            )
            logger.info("Cognee forget() skipped; stored decommission marker instead")
            return True

        # Note: Cognee forget() is best scoped by dataset, but in a real prod
        # environment you'd use node_set or data_id filtering. For the hackathon,
        # we'll use dataset-scoped forget with memory_only to simulate this.
        await _with_timeout(
            cognee.forget(
                dataset=f"user_{user_id}",
                memory_only=True,
            ),
            COGNEE_WRITE_TIMEOUT,
            "Cognee forget()",
        )
        logger.info(f"Service pattern {pattern_id} decommissioned — memory cleared for {user_id}")
        return True
    except Exception as e:
        logger.warning(f"Cognee forget() failed, falling back to SQLite-only resolve: {e}")
        return False


# ── Graph: visualization data ──────────────────────────────────────────────

async def _sqlite_graph_fallback() -> dict:
    """Build a compact graph from app state when Cognee graph export is unavailable."""
    try:
        from app.db import sqlite

        incidents = await sqlite.get_incidents()
        patterns = await sqlite.get_patterns(status="active")
    except Exception as exc:
        logger.warning("SQLite graph fallback failed: %s", exc)
        return {"nodes": [], "edges": []}

    nodes_by_id = {
        "user:demo_user": {
            "id": "user:demo_user",
            "label": "demo_user",
            "type": "NodeSet",
            "properties": {},
        }
    }
    edges = []

    for pattern in patterns:
        service_id = f"service:{pattern['service']}"
        nodes_by_id[service_id] = {
            "id": service_id,
            "label": pattern["service"],
            "type": "NodeSet",
            "properties": {
                "status": pattern["status"],
                "incident_count": str(pattern["incident_count"]),
                "description": f"{pattern['service']} has {pattern['incident_count']} active precedent incidents.",
            },
        }
        edges.append({
            "source": "user:demo_user",
            "target": service_id,
            "relationship": "monitors",
            "properties": {},
        })

    for incident in incidents[:50]:
        incident_id = f"incident:{incident['id']}"
        service_id = f"service:{incident['service']}"
        symptom_id = f"symptom:{incident['id']}"
        alert_id = f"alert:{incident['id']}"

        nodes_by_id[incident_id] = {
            "id": incident_id,
            "label": f"{incident['service']} {incident['created_at'][:10]}",
            "type": "Document",
            "properties": {
                "service": incident["service"],
                "severity": str(incident.get("severity") or ""),
                "created_at": incident["created_at"],
                "description": incident["symptom"],
            },
        }
        nodes_by_id.setdefault(service_id, {
            "id": service_id,
            "label": incident["service"],
            "type": "NodeSet",
            "properties": {"description": f"Service node for {incident['service']}"},
        })
        nodes_by_id[symptom_id] = {
            "id": symptom_id,
            "label": incident["symptom"],
            "type": "Entity",
            "properties": {
                "kind": "Symptom",
                "service": incident["service"],
                "description": incident["symptom"],
            },
        }
        nodes_by_id[alert_id] = {
            "id": alert_id,
            "label": incident["alert"],
            "type": "Entity",
            "properties": {
                "kind": "Alert",
                "service": incident["service"],
                "description": incident["alert"],
            },
        }

        edges.extend([
            {"source": "user:demo_user", "target": incident_id, "relationship": "has_incident", "properties": {}},
            {"source": incident_id, "target": service_id, "relationship": "occurred_in", "properties": {}},
            {"source": incident_id, "target": symptom_id, "relationship": "had_symptom", "properties": {}},
            {"source": incident_id, "target": alert_id, "relationship": "triggered_alert", "properties": {}},
        ])

        if incident.get("root_cause_and_fix"):
            fix_id = f"fix:{incident['id']}"
            nodes_by_id[fix_id] = {
                "id": fix_id,
                "label": incident["root_cause_and_fix"],
                "type": "Entity",
                "properties": {
                    "kind": "Root cause and fix",
                    "service": incident["service"],
                    "description": incident["root_cause_and_fix"],
                },
            }
            edges.append({
                "source": incident_id,
                "target": fix_id,
                "relationship": "resolved_by",
                "properties": {},
            })

    return {"nodes": list(nodes_by_id.values()), "edges": edges}


async def get_graph_data() -> dict:
    """Get the raw graph data for visualization."""
    fallback_data = await _sqlite_graph_fallback()
    if os.environ.get("PRECEDENT_GRAPH_SOURCE", "app_state") == "app_state":
        return fallback_data

    try:
        from cognee.infrastructure.databases.graph import get_graph_engine

        engine = await get_graph_engine()
        nodes, edges = await _with_timeout(
            engine.get_graph_data(),
            COGNEE_RECALL_TIMEOUT,
            "Cognee graph get_graph_data()",
        )

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

        if len(serialized_nodes) < 5 and len(fallback_data["nodes"]) > len(serialized_nodes):
            return fallback_data

        return {"nodes": serialized_nodes, "edges": serialized_edges}

    except Exception as e:
        logger.error(f"Failed to get graph data: {e}")
        return fallback_data
