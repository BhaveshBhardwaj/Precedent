"""Seed data for Precedent demo.

Populates ~18 backdated incidents across 3 fictional recurring services
so the precedent interrupt fires on the very first *live* entry during a demo.

Patterns:
1. "Cache Service" (Redis connection exhaustion) — 5 instances
2. "Payment Gateway" (Stripe timeout loops) — 4 instances
3. "Auth Service" (Token expiration sync issues) — 6 instances
   (includes 2 recent instances for decommission demo)

Run: python -m seed.seed_data
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta, timezone

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


# ── Seed incidents ────────────────────────────────────────────────────────────

def generate_seed_incidents():
    """Generate backdated seed incidents spread over the last 3 months."""
    now = datetime.now(timezone.utc)
    incidents = []

    # ── Pattern 1: Cache Service (Redis connection exhaustion) ────────────────
    cache_dates = [
        now - timedelta(days=85),
        now - timedelta(days=62),
        now - timedelta(days=41),
        now - timedelta(days=18),
        now - timedelta(days=5),
    ]

    cache_incidents = [
        {
            "symptom": "User login takes > 10 seconds. Timeout errors in frontend.",
            "alert": "cache-service CPU > 90%, Redis connection count maxed out",
            "severity": "high",
            "root_cause_and_fix": "Connection pool was not releasing connections on timeout. Restarted the Redis pods and increased pool timeout to 5s.",
        },
        {
            "symptom": "Dashboard completely unresponsive for 5 minutes.",
            "alert": "cache-service OOM kill and connection dropped",
            "severity": "critical",
            "root_cause_and_fix": "Same issue with connection pool exhaustion. Flushed Redis and restarted the service. Need to investigate why connections aren't closing.",
        },
        {
            "symptom": "Intermittent 502 Bad Gateway errors for authenticated users.",
            "alert": "High latency on cache-service, connection refused",
            "severity": "high",
            "root_cause_and_fix": "Redis max connections hit again. Added a temporary cron job to prune idle connections every 10 mins.",
        },
        {
            "symptom": "Spike in API latency, impacting checkout flow.",
            "alert": "cache-service Redis CPU 95%, thousands of TIME_WAIT sockets",
            "severity": "high",
            "root_cause_and_fix": "Rebooted Redis cluster. We keep hitting this pool exhaustion issue when traffic spikes.",
        },
        {
            "symptom": "Total cache failure, falling back to slow DB queries.",
            "alert": "cache-service unreachable, Redis instance frozen",
            "severity": "critical",
            "root_cause_and_fix": "Manual restart of the Redis nodes. The connection leak is still there.",
        },
    ]

    for i, (date, inc_data) in enumerate(zip(cache_dates, cache_incidents)):
        incidents.append({
            "id": str(uuid.uuid4()),
            "symptom": inc_data["symptom"],
            "alert": inc_data["alert"],
            "service": "cache-service",
            "severity": inc_data["severity"],
            "created_at": date.isoformat(),
            "root_cause_and_fix": inc_data["root_cause_and_fix"],
            "root_cause_logged_at": (date + timedelta(hours=2)).isoformat(),
        })

    # ── Pattern 2: Payment Gateway (Stripe timeout loops) ──────────────────
    payment_dates = [
        now - timedelta(days=78),
        now - timedelta(days=55),
        now - timedelta(days=30),
        now - timedelta(days=10),
    ]

    payment_incidents = [
        {
            "symptom": "Customers reporting double charges on checkout.",
            "alert": "payment-gateway 5xx error rate > 5%",
            "severity": "critical",
            "root_cause_and_fix": "Stripe API was slow, our client timed out and retried without idempotency keys. Added idempotency keys to the request headers.",
        },
        {
            "symptom": "Checkout page hanging indefinitely on submit.",
            "alert": "payment-gateway response time > 15s",
            "severity": "high",
            "root_cause_and_fix": "Webhook from Stripe was delayed. Our worker queue filled up waiting for webhook confirmation. Increased worker count.",
        },
        {
            "symptom": "More reports of users being charged twice but order not fulfilled.",
            "alert": "payment-gateway retries exceeding limit",
            "severity": "critical",
            "root_cause_and_fix": "Idempotency keys were improperly formatted. Rolled back the previous change and refunded the users manually.",
        },
        {
            "symptom": "Failed payments spiking.",
            "alert": "payment-gateway Stripe network timeout",
            "severity": "high",
            "root_cause_and_fix": "Stripe incident on their end. We just had to wait it out. Enabled fallback UI message.",
        },
    ]

    for i, (date, inc_data) in enumerate(zip(payment_dates, payment_incidents)):
        incidents.append({
            "id": str(uuid.uuid4()),
            "symptom": inc_data["symptom"],
            "alert": inc_data["alert"],
            "service": "payment-gateway",
            "severity": inc_data["severity"],
            "created_at": date.isoformat(),
            "root_cause_and_fix": inc_data["root_cause_and_fix"],
            "root_cause_logged_at": (date + timedelta(hours=1)).isoformat(),
        })

    # ── Pattern 3: Auth Service (Token expiration) ─────────────────────────────────
    auth_dates = [
        now - timedelta(days=82),
        now - timedelta(days=70),
        now - timedelta(days=58),
        now - timedelta(days=45),
        now - timedelta(days=25),  # fixed the issue!
        now - timedelta(days=8),   # monitoring the fix
    ]

    auth_incidents = [
        {
            "symptom": "Users randomly logged out while actively using the app.",
            "alert": "auth-service high rate of 401 Unauthorized",
            "severity": "medium",
            "root_cause_and_fix": "JWT token expiration was set to 15 mins but refresh token logic was failing. Extended JWT life to 1 hour as temporary fix.",
        },
        {
            "symptom": "Mobile app users forced to log in every day.",
            "alert": "auth-service refresh token endpoint 500 errors",
            "severity": "high",
            "root_cause_and_fix": "Database schema mismatch for the refresh token table. Dropped and recreated the index.",
        },
        {
            "symptom": "Cannot log in, endless spinner on login screen.",
            "alert": "auth-service latency > 5s for /login",
            "severity": "critical",
            "root_cause_and_fix": "Bcrypt hashing was eating all CPU. Scaled up the auth service pods from 2 to 6.",
        },
        {
            "symptom": "Users getting logged out again randomly.",
            "alert": "auth-service 401s spiking again",
            "severity": "medium",
            "root_cause_and_fix": "The new pods weren't sharing the same signing key secret. Restarted all pods with the correct env vars.",
        },
        {
            "symptom": "Investigating slow login times.",
            "alert": "auth-service DB query slow logs",
            "severity": "low",
            "root_cause_and_fix": "Finally migrated to the new auth provider (Auth0). Deprecated the old in-house auth logic.",
        },
        {
            "symptom": "Minor blip on legacy auth route.",
            "alert": "auth-service 404s on /legacy-login",
            "severity": "low",
            "root_cause_and_fix": "Just a straggler bot hitting the old endpoint. The Auth0 migration is fully complete and stable.",
        },
    ]

    for i, (date, inc_data) in enumerate(zip(auth_dates, auth_incidents)):
        incidents.append({
            "id": str(uuid.uuid4()),
            "symptom": inc_data["symptom"],
            "alert": inc_data["alert"],
            "service": "auth-service",
            "severity": inc_data["severity"],
            "created_at": date.isoformat(),
            "root_cause_and_fix": inc_data["root_cause_and_fix"],
            "root_cause_logged_at": (date + timedelta(hours=3)).isoformat(),
        })

    return incidents


def generate_seed_patterns():
    """Generate pattern records for the 3 seeded services."""
    now = datetime.now(timezone.utc)
    return [
        {
            "id": str(uuid.uuid4()),
            "label": "Redis connection leaks",
            "service": "cache-service",
            "incident_count": 5,
            "status": "active",
            "streak_started_at": (now - timedelta(days=85)).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "label": "Stripe timeout loops",
            "service": "payment-gateway",
            "incident_count": 4,
            "status": "active",
            "streak_started_at": (now - timedelta(days=78)).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "label": "Legacy Auth Instability",
            "service": "auth-service",
            "incident_count": 6,
            "status": "active",
            "streak_started_at": (now - timedelta(days=82)).isoformat(),
        },
    ]


async def dedupe_sqlite_seed_data(get_db) -> tuple[int, int]:
    """Remove duplicate seed rows while keeping one copy of each distinct item."""
    deleted_incidents = 0
    deleted_patterns = 0

    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT user_id, service, symptom, alert, COALESCE(root_cause_and_fix, '') AS root_cause_and_fix
            FROM incidents
            GROUP BY user_id, service, symptom, alert, COALESCE(root_cause_and_fix, '')
            HAVING COUNT(*) > 1
            """
        )
        duplicate_incident_groups = await cursor.fetchall()

        for group in duplicate_incident_groups:
            cursor = await db.execute(
                """
                SELECT id FROM incidents
                WHERE user_id = ? AND service = ? AND symptom = ? AND alert = ?
                  AND COALESCE(root_cause_and_fix, '') = ?
                ORDER BY created_at DESC, id DESC
                """,
                (
                    group["user_id"],
                    group["service"],
                    group["symptom"],
                    group["alert"],
                    group["root_cause_and_fix"],
                ),
            )
            rows = await cursor.fetchall()
            ids_to_delete = [row["id"] for row in rows[1:]]
            for incident_id in ids_to_delete:
                await db.execute("DELETE FROM incidents WHERE id = ?", (incident_id,))
            deleted_incidents += len(ids_to_delete)

        cursor = await db.execute(
            """
            SELECT user_id, service, status
            FROM patterns
            GROUP BY user_id, service, status
            HAVING COUNT(*) > 1
            """
        )
        duplicate_pattern_groups = await cursor.fetchall()

        for group in duplicate_pattern_groups:
            cursor = await db.execute(
                """
                SELECT id, incident_count, streak_started_at, decommissioned_at
                FROM patterns
                WHERE user_id = ? AND service = ? AND status = ?
                ORDER BY incident_count DESC, COALESCE(streak_started_at, '') ASC, id DESC
                """,
                (group["user_id"], group["service"], group["status"]),
            )
            rows = await cursor.fetchall()
            if not rows:
                continue

            keep = rows[0]
            ids_to_delete = [row["id"] for row in rows[1:]]
            await db.execute(
                """
                UPDATE patterns
                SET incident_count = ?,
                    streak_started_at = COALESCE(streak_started_at, ?),
                    decommissioned_at = COALESCE(decommissioned_at, ?)
                WHERE id = ?
                """,
                (
                    keep["incident_count"],
                    keep["streak_started_at"],
                    keep["decommissioned_at"],
                    keep["id"],
                ),
            )
            for pattern_id in ids_to_delete:
                await db.execute("DELETE FROM patterns WHERE id = ?", (pattern_id,))
            deleted_patterns += len(ids_to_delete)

        await db.commit()
    finally:
        await db.close()

    return deleted_incidents, deleted_patterns


async def seed():
    """Run the seed process without deleting existing data or exhausting LLM rate limits."""
    print("Precedent Safe Seed Script")
    print("=" * 50)

    from app.db.sqlite import init_db, create_incident_with_timestamp, create_pattern, get_db
    await init_db()
    print("SQLite initialized")

    from app.cognee_client import init_cognee
    await init_cognee()
    print("Cognee initialized")

    incidents = generate_seed_incidents()
    patterns = generate_seed_patterns()

    print(f"\nEnsuring {len(incidents)} demo incidents across {len(patterns)} services...")

    inserted_incidents = 0
    skipped_incidents = 0

    for incident in incidents:
        db = await get_db()
        try:
            cursor = await db.execute(
                """
                SELECT id FROM incidents
                WHERE user_id = ? AND service = ? AND symptom = ? AND alert = ?
                LIMIT 1
                """,
                (
                    incident.get("user_id", "demo_user"),
                    incident["service"],
                    incident["symptom"],
                    incident["alert"],
                ),
            )
            exists = await cursor.fetchone()
        finally:
            await db.close()

        if exists:
            skipped_incidents += 1
            continue

        await create_incident_with_timestamp(**incident)
        inserted_incidents += 1

    print(f"SQLite incidents: {inserted_incidents} inserted, {skipped_incidents} already present")

    print(f"\nEnsuring {len(patterns)} service pattern records...")
    inserted_patterns = 0
    skipped_patterns = 0
    for pattern in patterns:
        db = await get_db()
        try:
            cursor = await db.execute(
                """
                SELECT id, incident_count FROM patterns
                WHERE user_id = ? AND service = ? AND status = ?
                LIMIT 1
                """,
                (pattern.get("user_id", "demo_user"), pattern["service"], pattern["status"]),
            )
            existing_pattern = await cursor.fetchone()
            if existing_pattern:
                await db.execute(
                    "UPDATE patterns SET incident_count = MAX(incident_count, ?) WHERE id = ?",
                    (pattern["incident_count"], existing_pattern["id"]),
                )
                await db.commit()
                skipped_patterns += 1
                continue
        finally:
            await db.close()

        await create_pattern(**pattern)
        inserted_patterns += 1

    print(f"SQLite patterns: {inserted_patterns} inserted, {skipped_patterns} already present")

    deleted_incidents, deleted_patterns = await dedupe_sqlite_seed_data(get_db)
    print(f"SQLite duplicates removed: {deleted_incidents} incidents, {deleted_patterns} patterns")

    print("\nBuilding Cognee graph from local seed data (no LLM/Groq calls)...")
    try:
        from seed.local_graph_builder import main as build_local_graph

        await build_local_graph()
        print("Cognee graph build complete")
    except Exception as e:
        print(f"Cognee local graph build failed (backend SQLite fallback remains usable): {e}")

    print("\n" + "=" * 50)
    print("Seed complete! Ready for demo.")
    print("   Start the backend: uvicorn app.main:app --reload --port 8000")
    print("   Start the frontend: cd ../frontend && npm run dev")


if __name__ == "__main__":
    asyncio.run(seed())
