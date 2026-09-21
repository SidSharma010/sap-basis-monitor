#!/usr/bin/env python3
"""
analyze_output.py

Dependency-free threshold engine for SAP Basis monitoring metrics.

Takes a structured JSON snapshot (the kind connectors/hana_monitor.py or
connectors/s4hana_odata_monitor.py produce, or one you build by hand from
transaction output) and classifies each metric against configurable
severity thresholds, returning a prioritized issue list.

This does NOT parse raw SM21/ST22 log text -- log formats vary too much
across systems, releases, and languages to regex reliably, and a script
that silently mis-parses a real syslog is worse than no script at all.
Raw log/dump text is meant to be read directly by a Claude session
running the sap-basis-monitor skill, which can use judgment the way a
strict regex can't. This script covers the structured-metrics half of
monitoring: disk, memory, jobs, locks, backups, work processes.

Usage:
    python analyze_output.py path/to/snapshot.json
    cat snapshot.json | python analyze_output.py

Expected input shape (all keys optional -- only present metrics are checked):
{
  "disk_usage_pct": {"data": 78, "log": 45},
  "used_memory_pct": 82,
  "failed_jobs": ["ZBACKUP_NIGHTLY", "ZINTERFACE_SYNC"],
  "cancelled_jobs": [],
  "dumps_last_24h": 3,
  "lock_wait_max_seconds": 12,
  "backup_last_success_hours_ago": 18,
  "free_dialog_work_process_pct": 35,
  "active_connections": 210
}
"""

import json
import sys

# Thresholds are a starting point, not a verified SLA standard for any
# specific system -- tune them for your own environment. See
# references/severity-thresholds.md for the reasoning behind each one.
THRESHOLDS = {
    "disk_usage_pct": {"warning": 80, "critical": 90, "direction": "above"},
    "used_memory_pct": {"warning": 85, "critical": 95, "direction": "above"},
    "dumps_last_24h": {"warning": 5, "critical": 20, "direction": "above"},
    "lock_wait_max_seconds": {"warning": 60, "critical": 300, "direction": "above"},
    "backup_last_success_hours_ago": {"warning": 24, "critical": 48, "direction": "above"},
    "free_dialog_work_process_pct": {"warning": 20, "critical": 10, "direction": "below"},
}

RECOMMENDATIONS = {
    "disk_usage_pct": "Check the volume in references/hana-system-views.md (M_DISK_USAGE). Plan a resize or archive/cleanup before it hits 100%.",
    "used_memory_pct": "Check M_SERVICE_MEMORY per service. Look for a runaway statement or column store not being unloaded before assuming you need more RAM.",
    "failed_jobs": "See references/classic-tcodes.md (SM37). Check the job log for the actual ABAP error, not just 'failed' -- root cause first, rerun second.",
    "cancelled_jobs": "Cancelled usually means someone stopped it or it hit a runtime/resource limit. Check who/what cancelled it before rescheduling blind.",
    "dumps_last_24h": "See references/classic-tcodes.md (ST22). A cluster of the same dump type points to one root cause, not many separate problems.",
    "lock_wait_max_seconds": "See references/classic-tcodes.md (SM12). Identify the blocking session before killing anything -- killing the wrong lock holder can cause data inconsistency.",
    "backup_last_success_hours_ago": "Check M_BACKUP_CATALOG for the actual failure reason, not just 'overdue'. This is usually a page-one priority regardless of other metrics.",
    "free_dialog_work_process_pct": "See references/classic-tcodes.md (SM50/SM66). Low free work processes usually means something long-running is hogging them -- find it before adding more processes.",
}

def classify_scalar(name, value):
    rule = THRESHOLDS.get(name)
    if rule is None or value is None:
        return None

    direction = rule["direction"]
    if direction == "above":
        if value >= rule["critical"]:
            severity = "critical"
        elif value >= rule["warning"]:
            severity = "warning"
        else:
            return None
    else:  # "below"
        if value <= rule["critical"]:
            severity = "critical"
        elif value <= rule["warning"]:
            severity = "warning"
        else:
            return None

    return {
        "metric": name,
        "value": value,
        "severity": severity,
        "recommendation": RECOMMENDATIONS.get(name, ""),
    }

def analyze(data: dict) -> dict:
    issues = []

    # Scalar/threshold metrics
    for name in THRESHOLDS:
        raw = data.get(name)
        if raw is None:
            continue
        if isinstance(raw, dict):
            # e.g. disk_usage_pct broken down per volume: {"data": 78, "log": 45}
            for sub_label, sub_value in raw.items():
                result = classify_scalar(name, sub_value)
                if result:
                    result["metric"] = f"{name}.{sub_label}"
                    issues.append(result)
        else:
            result = classify_scalar(name, raw)
            if result:
                issues.append(result)

    # List-type metrics: any non-empty list is itself the issue
    for name in ("failed_jobs", "cancelled_jobs"):
        items = data.get(name)
        if items:
            issues.append({
                "metric": name,
                "value": items,
                "severity": "critical" if name == "failed_jobs" else "warning",
                "recommendation": RECOMMENDATIONS.get(name, ""),
            })

    severity_order = {"critical": 0, "warning": 1}
    issues.sort(key=lambda i: severity_order.get(i["severity"], 2))

    return {
        "issue_count": len(issues),
        "critical_count": sum(1 for i in issues if i["severity"] == "critical"),
        "warning_count": sum(1 for i in issues if i["severity"] == "warning"),
        "issues": issues,
        "healthy": len(issues) == 0,
    }

def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            raw = f.read()
    else:
        raw = sys.stdin.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}, indent=2))
        sys.exit(1)

    result = analyze(data)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["healthy"] or result["critical_count"] == 0 else 1)


if __name__ == "__main__":
    main()

