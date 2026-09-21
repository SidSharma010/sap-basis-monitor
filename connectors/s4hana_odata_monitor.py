#!/usr/bin/env python3
"""
s4hana_odata_monitor.py

Pulls application-server-level monitoring data (background jobs, etc.)
from an S/4HANA (or NetWeaver) system over its standard OData/REST
Gateway interface, and prints it as JSON in the shape
lib/analyze_output.py expects.

Honest note on service names: SAP Gateway (OData) service names differ
by release, industry solution, and what your Basis team has activated --
there is no single universal "job monitoring" service name that's
guaranteed to exist on every system. This script does NOT hardcode one.
Instead, point --service-url at whatever your own system actually
exposes. Find yours via:
  - Transaction /IWFND/MAINT_SERVICE (list of activated Gateway services), or
  - The SAP API Business Hub (api.sap.com) for your product/release, or
  - Your Basis/Integration team, if someone else activated it.

A common, broadly available example (verify it exists on YOUR system
before relying on it) is the generic Application Log OData service.
Whatever you point this at, the entity set just needs to return records
with a status/severity field this script can count.

Install:
    pip install requests

Usage:
    python s4hana_odata_monitor.py \\
        --service-url "https://myhost:port/sap/opu/odata/sap/YOUR_SERVICE_SRV" \\
        --entity-set "YourEntitySet" \\
        --user MONITOR_USER --password '***'

    Or set env vars: S4H_SERVICE_URL, S4H_ENTITY_SET, S4H_USER, S4H_PASSWORD

Auth: this uses HTTP Basic auth for simplicity. Production setups should
use OAuth2/SAML where the Gateway system supports it -- Basic auth over
plain HTTP is never acceptable; always use HTTPS.
"""

import argparse
import json
import os
import sys

try:
    import requests
except ImportError:
    print(json.dumps({"error": "requests not installed. Run: pip install requests"}), file=sys.stderr)
    sys.exit(1)


def fetch_entity_set(service_url, entity_set, user, password, filter_expr=None):
    url = service_url.rstrip("/") + "/" + entity_set.lstrip("/")
    params = {"$format": "json"}
    if filter_expr:
        params["$filter"] = filter_expr

    resp = requests.get(
        url,
        params=params,
        auth=(user, password),
        headers={"Accept": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    # Classic OData v2 wraps results in {"d": {"results": [...]}}
    return body.get("d", {}).get("results", body.get("value", []))


def build_snapshot(service_url, entity_set, user, password, status_field, failed_values, cancelled_values):
    records = fetch_entity_set(service_url, entity_set, user, password)

    failed_jobs = []
    cancelled_jobs = []
    for r in records:
        status = str(r.get(status_field, "")).strip().upper()
        name = r.get("JobName") or r.get("Name") or r.get("name") or str(r)
        if status in [v.upper() for v in failed_values]:
            failed_jobs.append(name)
        elif status in [v.upper() for v in cancelled_values]:
            cancelled_jobs.append(name)

    return {
        "failed_jobs": failed_jobs,
        "cancelled_jobs": cancelled_jobs,
    }

def main():
    parser = argparse.ArgumentParser(description="Snapshot job/log status from a Gateway OData service as JSON.")
    parser.add_argument("--service-url", default=os.environ.get("S4H_SERVICE_URL"))
    parser.add_argument("--entity-set", default=os.environ.get("S4H_ENTITY_SET"))
    parser.add_argument("--user", default=os.environ.get("S4H_USER"))
    parser.add_argument("--password", default=os.environ.get("S4H_PASSWORD"))
    parser.add_argument("--status-field", default="Status",
                         help="Name of the field in the entity set that holds job/log status (default: Status)")
    parser.add_argument("--failed-values", default="FAILED,ERROR",
                         help="Comma-separated status values that count as failed")
    parser.add_argument("--cancelled-values", default="CANCELLED,CANCELED",
                         help="Comma-separated status values that count as cancelled")
    args = parser.parse_args()

    missing = [n for n in ("service_url", "entity_set", "user", "password") if not getattr(args, n)]
    if missing:
        print(json.dumps({"error": f"Missing required arguments: {', '.join(missing)}"}), file=sys.stderr)
        sys.exit(1)

    try:
        snapshot = build_snapshot(
            args.service_url,
            args.entity_set,
            args.user,
            args.password,
            args.status_field,
            args.failed_values.split(","),
            args.cancelled_values.split(","),
        )
    except requests.exceptions.HTTPError as e:
        print(json.dumps({"error": f"HTTP error calling service: {e}"}), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()

