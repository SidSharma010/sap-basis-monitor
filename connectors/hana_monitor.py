#!/usr/bin/env python3
"""
hana_monitor.py

Pulls a snapshot of key SAP HANA health metrics using SAP's official
hdbcli Python client and prints it as JSON in the shape
lib/analyze_output.py expects.

This script only ever runs SELECT queries against HANA's public
monitoring system views (the M_* views under the SYS schema). It makes
no changes to the target system and needs no special privileges beyond
a login that can SELECT from those views (typically the MONITORING role,
or a custom role scoped to just these views -- do not use SYSTEM for
this).

Install:
    pip install hdbcli

Usage:
    python hana_monitor.py --host myhana.example.com --port 30015 \\
        --user MONITOR_USER --password '***'

    Or set env vars instead of flags:
        HANA_HOST, HANA_PORT, HANA_USER, HANA_PASSWORD

    Pipe straight into the triage engine:
        python hana_monitor.py --host ... --user ... --password ... \\
            | python ../lib/analyze_output.py

Column names below match the documented M_SERVICE_MEMORY and
M_DISK_USAGE views as of this writing. SAP has, in the past, added or
renamed columns between HANA revisions -- if a query errors on a missing
column, run `SELECT * FROM <view> LIMIT 1` first to see what your
revision actually exposes, and adjust.
"""

import argparse
import json
import os
import sys

try:
    from hdbcli import dbapi
except ImportError:
    print(
        json.dumps({"error": "hdbcli not installed. Run: pip install hdbcli"}),
        file=sys.stderr,
    )
    sys.exit(1)


def get_connection(host, port, user, password):
    return dbapi.connect(address=host, port=port, user=user, password=password)


def fetch_memory(cursor):
    cursor.execute("""
        SELECT ROUND(SUM(TOTAL_MEMORY_USED_SIZE) / NULLIF(SUM(ALLOCATION_LIMIT), 0) * 100, 1)
        FROM SYS.M_SERVICE_MEMORY
    """)
    row = cursor.fetchone()
    return float(row[0]) if row and row[0] is not None else None


def fetch_disk_usage(cursor):
    # PATH / USAGE_TYPE naming can vary slightly; USAGE_TYPE typically
    # includes values like 'DATA' and 'LOG'.
    cursor.execute("""
        SELECT USAGE_TYPE, ROUND(SUM(USED_SIZE) / NULLIF(SUM(TOTAL_SIZE), 0) * 100, 1)
        FROM SYS.M_DISK_USAGE
        GROUP BY USAGE_TYPE
    """)
    result = {}
    for usage_type, pct in cursor.fetchall():
        if usage_type and pct is not None:
            key = str(usage_type).strip().lower()
            key = "data" if "data" in key else ("log" if "log" in key else key)
            result[key] = float(pct)
    return result

def fetch_connections(cursor):
    cursor.execute("""
        SELECT COUNT(*) FROM SYS.M_CONNECTIONS WHERE CONNECTION_STATUS = 'RUNNING'
    """)
    row = cursor.fetchone()
    return int(row[0]) if row and row[0] is not None else None


def fetch_backup_age_hours(cursor):
    cursor.execute("""
        SELECT TOP 1 SYS_START_TIME
        FROM SYS.M_BACKUP_CATALOG
        WHERE ENTRY_TYPE_NAME = 'complete data backup' AND STATE_NAME = 'successful'
        ORDER BY SYS_START_TIME DESC
    """)
    row = cursor.fetchone()
    if not row or row[0] is None:
        return None
    from datetime import datetime, timezone
    last = row[0]
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - last
    return round(delta.total_seconds() / 3600, 1)


def build_snapshot(cursor):
    return {
        "used_memory_pct": fetch_memory(cursor),
        "disk_usage_pct": fetch_disk_usage(cursor),
        "active_connections": fetch_connections(cursor),
        "backup_last_success_hours_ago": fetch_backup_age_hours(cursor),
        # failed_jobs / cancelled_jobs / dumps_last_24h / lock_wait_max_seconds /
        # free_dialog_work_process_pct are ABAP-stack concepts (SM37, ST22, SM12,
        # SM50) with no HANA-DB-level equivalent -- pull those via
        # s4hana_odata_monitor.py against the application server instead, or
        # from a manual transaction paste. A pure HANA-only landscape (no ABAP
        # stack) won't have these at all, which is expected.
    }

def main():
    parser = argparse.ArgumentParser(description="Snapshot key SAP HANA health metrics as JSON.")
    parser.add_argument("--host", default=os.environ.get("HANA_HOST"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("HANA_PORT", "30015")))
    parser.add_argument("--user", default=os.environ.get("HANA_USER"))
    parser.add_argument("--password", default=os.environ.get("HANA_PASSWORD"))
    args = parser.parse_args()

    missing = [name for name in ("host", "user", "password") if not getattr(args, name)]
    if missing:
        print(json.dumps({"error": f"Missing required connection info: {', '.join(missing)}"}), file=sys.stderr)
        sys.exit(1)

    conn = get_connection(args.host, args.port, args.user, args.password)
    try:
        cursor = conn.cursor()
        snapshot = build_snapshot(cursor)
    finally:
        conn.close()

    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()

