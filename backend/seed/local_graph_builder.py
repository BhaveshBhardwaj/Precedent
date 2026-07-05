import asyncio
import sys
import os
import sqlite3
import uuid
from datetime import datetime, timezone

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cognee.infrastructure.databases.graph import get_graph_engine
from cognee.infrastructure.engine import DataPoint

class CogneeNode(DataPoint):
    name: str
    type: str

async def main():
    print("==================================================")
    print("Cognee Local Graph Builder (Bypassing LLM Rate Limits)")
    print("==================================================")

    # 1. Connect to SQLite to read existing incidents
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "precedent.db")
    if not os.path.exists(db_path):
        print(f"Error: SQLite database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, symptom, alert, service, severity, created_at, root_cause_and_fix FROM incidents")
        incidents = cursor.fetchall()
    except Exception as e:
        print(f"Error reading SQLite: {e}")
        conn.close()
        return

    conn.close()

    if not incidents:
        print("No incidents found in SQLite. Please seed SQLite first.")
        return

    print(f"Found {len(incidents)} incidents in SQLite. Building Cognee graph...")

    # 2. Get Cognee Graph Engine
    try:
        engine = await get_graph_engine()
        print(f"Connected to Cognee graph engine: {type(engine).__name__}")
    except Exception as e:
        print(f"Failed to connect to graph engine: {e}")
        return

    # 3. Create nodes and edges lists
    nodes = []
    edges = []

    # Add User NodeSet (Green)
    user_id = "demo_user"
    user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"user:{user_id}")
    nodes.append(CogneeNode(id=user_uuid, name=f"User: {user_id}", type="NodeSet"))

    # Add unique services tracking to avoid redundant nodes
    added_services = set()
    added_symptoms = set()
    added_alerts = set()
    added_fixes = set()
    added_events = set()

    for row in incidents:
        inc_id, symptom, alert, service, severity, created_at, root_cause_and_fix = row

        # Incident Document Node (Pink)
        incident_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"incident:{inc_id}")
        nodes.append(CogneeNode(
            id=incident_uuid,
            name=f"Incident: {service} ({created_at[:10]})",
            type="Document"
        ))

        # Link Incident to User
        edges.append((str(user_uuid), str(incident_uuid), "has_incident", {}))

        # Service NodeSet (Green)
        if service not in added_services:
            service_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"service:{service}")
            nodes.append(CogneeNode(id=service_uuid, name=service, type="NodeSet"))
            added_services.add(service)
            # Link User to Service
            edges.append((str(user_uuid), str(service_uuid), "monitors", {}))

        service_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"service:{service}")
        # Link Incident to Service
        edges.append((str(incident_uuid), str(service_uuid), "occurred_in", {}))

        # Symptom Node (Purple Entity)
        if symptom:
            symptom_key = f"symptom:{symptom}"
            if symptom_key not in added_symptoms:
                symptom_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, symptom_key)
                nodes.append(CogneeNode(id=symptom_uuid, name=symptom, type="Entity"))
                added_symptoms.add(symptom_key)
            symptom_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, symptom_key)
            edges.append((str(incident_uuid), str(symptom_uuid), "had_symptom", {}))

        # Alert Node (Purple Entity)
        if alert:
            alert_key = f"alert:{alert}"
            if alert_key not in added_alerts:
                alert_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, alert_key)
                nodes.append(CogneeNode(id=alert_uuid, name=alert, type="Entity"))
                added_alerts.add(alert_key)
            alert_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, alert_key)
            edges.append((str(incident_uuid), str(alert_uuid), "triggered_alert", {}))

        # Root Cause / Fix Node (Purple Entity)
        if root_cause_and_fix:
            fix_key = f"fix:{root_cause_and_fix}"
            if fix_key not in added_fixes:
                fix_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, fix_key)
                nodes.append(CogneeNode(id=fix_uuid, name=root_cause_and_fix, type="Entity"))
                added_fixes.add(fix_key)
            fix_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, fix_key)
            edges.append((str(incident_uuid), str(fix_uuid), "resolved_by", {}))

        # Event Node (Amber Event)
        if created_at:
            event_key = f"event:{created_at}"
            if event_key not in added_events:
                event_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, event_key)
                nodes.append(CogneeNode(id=event_uuid, name=created_at, type="Event"))
                added_events.add(event_key)
            event_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, event_key)
            edges.append((str(incident_uuid), str(event_uuid), "happened_at", {}))

    print(f"Created {len(nodes)} graph nodes and {len(edges)} graph edges.")

    # 4. Insert into Cognee DB
    try:
        await engine.add_nodes(nodes)
        print("Graph nodes written successfully.")
        await engine.add_edges(edges)
        print("Graph edges written successfully.")
        print("Check-pointing graph database...")
        await engine.checkpoint()
        print("==================================================")
        print("Graph built successfully! Direct Cognee seeding complete.")
        print("==================================================")
    except Exception as e:
        print(f"Failed to write graph: {e}")

if __name__ == "__main__":
    asyncio.run(main())
