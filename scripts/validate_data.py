#!/usr/bin/env python3
"""
validate_data.py - Verify data completeness before cost calculation

Purpose: Catch incomplete data and prevent assumptions

This prevents mistake #5 from original analysis:
Speculating about missing data instead of flagging it clearly.

Usage: ./validate_data.py <metrics_json_file>
"""

import json
import sys
from typing import Dict, List, Tuple
from datetime import datetime

# Expected metrics per service
SERVICE_METRICS = {
    "firestore": [
        "firestore.googleapis.com/document/read_count",
        "firestore.googleapis.com/document/write_count",
        "firestore.googleapis.com/document/delete_count",
        "firestore.googleapis.com/storage/total_bytes",
    ],
    "rtdb": [
        "firebasedatabase.googleapis.com/network/monthly_sent",
        "firebasedatabase.googleapis.com/storage/total_bytes",
        "firebasedatabase.googleapis.com/network/api_hits_count",
    ],
    "functions": [
        "cloudfunctions.googleapis.com/function/execution_count",
        "cloudfunctions.googleapis.com/function/execution_times",
        "cloudfunctions.googleapis.com/function/active_instances",
    ],
    "bigquery": [
        "bigquery.googleapis.com/storage/stored_bytes",
        "bigquery.googleapis.com/query/count",
        "bigquery.googleapis.com/query/scanned_bytes",
    ],
    "storage": [
        "storage.googleapis.com/storage/total_bytes",
        "storage.googleapis.com/network/sent_bytes_count",
        "storage.googleapis.com/api/request_count",
    ],
    "cloudrun": [
        "run.googleapis.com/request_count",
        "run.googleapis.com/container/instance_count",
        "run.googleapis.com/container/billable_instance_time",
    ],
}


def validate_metrics(metrics: Dict, service: str) -> Tuple[int, List[str], List[str]]:
    """
    Validate metrics completeness.

    Returns:
        (completeness_score, missing_metrics, warnings)
    """
    expected = SERVICE_METRICS.get(service, [])
    if not expected:
        return 0, [f"Unknown service: {service}"], []

    missing = []
    warnings = []

    for metric in expected:
        if metric not in metrics:
            missing.append(f"MISSING: {metric}")
        elif metrics[metric] is None:
            missing.append(f"NULL: {metric} (API returned null)")
        elif metrics[metric] == 0:
            # Zero might be legitimate, but flag it
            warnings.append(f"ZERO: {metric} = 0 (verify this is correct)")

    if not missing:
        score = 100
    else:
        score = int((1 - len(missing) / len(expected)) * 100)

    return score, missing, warnings


def validate_date_range(data: Dict) -> List[str]:
    """Verify dates are reasonable."""
    issues = []

    start = data.get("start_date", "")
    end = data.get("end_date", "")

    if not start or not end:
        issues.append("Missing start_date or end_date")
        return issues

    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))

        # Check range makes sense
        if end_dt <= start_dt:
            issues.append(f"End date ({end}) is not after start date ({start})")

        # Check if range is too short (less than 1 day)
        delta = end_dt - start_dt
        if delta.total_seconds() < 86400:  # 24 hours
            issues.append(f"Date range is very short: {delta.total_seconds() / 3600:.1f} hours")

        # Check if range is partial month (for monthly analysis)
        if start_dt.day != 1:
            issues.append(f"Start date is not first of month: {start}")

    except Exception as e:
        issues.append(f"Invalid date format: {e}")

    return issues


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_data.py <metrics.json>", file=sys.stderr)
        sys.exit(1)

    metrics_file = sys.argv[1]

    try:
        with open(metrics_file) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {metrics_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    service = data.get("service", "unknown")
    metrics = data.get("metrics", {})

    # Validate metrics
    score, missing, warnings = validate_metrics(metrics, service)

    # Validate date range
    date_issues = validate_date_range(data)

    # Build report
    report = {
        "file": metrics_file,
        "service": service,
        "project_id": data.get("project_id", "unknown"),
        "date_range": {
            "start": data.get("start_date", "unknown"),
            "end": data.get("end_date", "unknown"),
        },
        "validation": {
            "completeness_score": score,
            "missing_metrics": missing,
            "warnings": warnings,
            "date_range_issues": date_issues,
        },
        "passed": score == 100 and len(date_issues) == 0,
        "validation_time": datetime.utcnow().isoformat() + "Z",
    }

    # Output report
    print(json.dumps(report, indent=2))

    # Exit code
    if report["passed"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
