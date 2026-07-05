"""SQLite database layer for app state (incidents, patterns).

Cognee owns the semantic/graph memory. SQLite backs the UI list views
and is NOT the source of truth for pattern detection.
"""

import aiosqlite
import os
from typing import Optional, List
from datetime import datetime, timezone

DB_PATH = os.environ.get("DATABASE_URL", "sqlite:///./precedent.db").replace("sqlite:///", "")
if not DB_PATH or DB_PATH == "./precedent.db":
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "precedent.db")


async def get_db() -> aiosqlite.Connection:
    """Get a database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """Initialize the database schema."""
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'demo_user',
                symptom TEXT NOT NULL,
                alert TEXT NOT NULL,
                service TEXT NOT NULL,
                severity TEXT,
                created_at TEXT NOT NULL,
                root_cause_and_fix TEXT,
                root_cause_logged_at TEXT
            );

            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'demo_user',
                label TEXT NOT NULL,
                service TEXT NOT NULL,
                incident_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                streak_started_at TEXT,
                decommissioned_at TEXT
            );
        """)
        await db.commit()
    finally:
        await db.close()


# ── Incident CRUD ──────────────────────────────────────────────────────────────

async def create_incident(
    id: str,
    symptom: str,
    alert: str,
    service: str,
    severity: Optional[str] = None,
    user_id: str = "demo_user",
) -> dict:
    """Insert a new incident and return it."""
    created_at = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO incidents (id, user_id, symptom, alert, service, severity, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (id, user_id, symptom, alert, service, severity, created_at),
        )
        await db.commit()
        return {
            "id": id,
            "user_id": user_id,
            "symptom": symptom,
            "alert": alert,
            "service": service,
            "severity": severity,
            "created_at": created_at,
            "root_cause_and_fix": None,
            "root_cause_logged_at": None,
        }
    finally:
        await db.close()


async def create_incident_with_timestamp(
    id: str,
    symptom: str,
    alert: str,
    service: str,
    created_at: str,
    severity: Optional[str] = None,
    root_cause_and_fix: Optional[str] = None,
    root_cause_logged_at: Optional[str] = None,
    user_id: str = "demo_user",
) -> dict:
    """Insert a backdated incident (used by seed script)."""
    db = await get_db()
    try:
        await db.execute(
            """INSERT OR REPLACE INTO incidents
               (id, user_id, symptom, alert, service, severity, created_at, root_cause_and_fix, root_cause_logged_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (id, user_id, symptom, alert, service, severity, created_at, root_cause_and_fix, root_cause_logged_at),
        )
        await db.commit()
        return {
            "id": id,
            "user_id": user_id,
            "symptom": symptom,
            "alert": alert,
            "service": service,
            "severity": severity,
            "created_at": created_at,
            "root_cause_and_fix": root_cause_and_fix,
            "root_cause_logged_at": root_cause_logged_at,
        }
    finally:
        await db.close()


async def get_incidents(user_id: str = "demo_user") -> List[dict]:
    """Get all incidents for a user, newest first."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, user_id, symptom, alert, service, severity,
                      created_at, root_cause_and_fix, root_cause_logged_at
               FROM incidents WHERE user_id = ? ORDER BY created_at DESC""",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_incident(incident_id: str) -> Optional[dict]:
    """Get a single incident by ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, user_id, symptom, alert, service, severity,
                      created_at, root_cause_and_fix, root_cause_logged_at
               FROM incidents WHERE id = ?""",
            (incident_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def update_root_cause(incident_id: str, root_cause_and_fix: str) -> Optional[dict]:
    """Update the root cause of an incident."""
    root_cause_logged_at = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            "UPDATE incidents SET root_cause_and_fix = ?, root_cause_logged_at = ? WHERE id = ?",
            (root_cause_and_fix, root_cause_logged_at, incident_id),
        )
        await db.commit()
        return await get_incident(incident_id)
    finally:
        await db.close()


async def get_incident_count(user_id: str = "demo_user") -> int:
    """Get total incident count for a user."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM incidents WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row["count"] if row else 0
    finally:
        await db.close()


# ── Pattern CRUD ────────────────────────────────────────────────────────────

async def create_pattern(
    id: str,
    label: str,
    service: str,
    incident_count: int = 0,
    user_id: str = "demo_user",
    status: str = "active",
    streak_started_at: Optional[str] = None,
) -> dict:
    """Create a new pattern."""
    if streak_started_at is None:
        streak_started_at = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            """INSERT OR REPLACE INTO patterns (id, user_id, label, service, incident_count, status, streak_started_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (id, user_id, label, service, incident_count, status, streak_started_at),
        )
        await db.commit()
        return {
            "id": id,
            "user_id": user_id,
            "label": label,
            "service": service,
            "incident_count": incident_count,
            "status": "active",
            "streak_started_at": streak_started_at,
            "decommissioned_at": None,
        }
    finally:
        await db.close()


async def get_patterns(user_id: str = "demo_user", status: Optional[str] = None) -> List[dict]:
    """Get patterns for a user, optionally filtered by status."""
    db = await get_db()
    try:
        if status:
            cursor = await db.execute(
                "SELECT * FROM patterns WHERE user_id = ? AND status = ? ORDER BY incident_count DESC",
                (user_id, status),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM patterns WHERE user_id = ? ORDER BY incident_count DESC",
                (user_id,),
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_pattern(pattern_id: str) -> Optional[dict]:
    """Get a single pattern by ID."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM patterns WHERE id = ?", (pattern_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def decommission_service(pattern_id: str) -> Optional[dict]:
    """Mark a service pattern as decommissioned."""
    decommissioned_at = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            "UPDATE patterns SET status = 'decommissioned', decommissioned_at = ? WHERE id = ?",
            (decommissioned_at, pattern_id),
        )
        await db.commit()
        return await get_pattern(pattern_id)
    finally:
        await db.close()


async def increment_pattern_count(pattern_id: str) -> None:
    """Increment the incident count for a pattern."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE patterns SET incident_count = incident_count + 1 WHERE id = ?",
            (pattern_id,),
        )
        await db.commit()
    finally:
        await db.close()
