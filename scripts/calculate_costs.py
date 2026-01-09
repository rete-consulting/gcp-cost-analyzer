#!/usr/bin/env python3
"""
calculate_costs.py - Calculate GCP costs with free tier accounting

Purpose: Accurate cost calculation matching billing API

This implements what WORKED in the original analysis:
- Service-specific pricing formulas
- Free tier deductions (50K reads/day, etc.)
- Calculation that matched billing within $0.60

Usage: ./calculate_costs.py <metrics.json> <days_in_month>
"""

import json
import sys
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class CostBreakdown:
    """Cost breakdown for a service."""

    service: str
    total_cost: float
    components: Dict[str, float]
    free_tier_savings: float
    billable_usage: Dict[str, Any]
    pricing_notes: list


def calculate_firestore_costs(metrics: Dict, days: int) -> CostBreakdown:
    """
    Calculate Firestore costs with free tier.

    Free tier (per day):
    - 50,000 reads
    - 20,000 writes
    - 20,000 deletes
    - 1 GiB storage

    Pricing (multi-region):
    - $0.06 per 100K reads
    - $0.18 per 100K writes
    - $0.02 per 100K deletes
    - $0.18 per GiB storage/month
    """
    reads = metrics.get("firestore.googleapis.com/document/read_count", 0)
    writes = metrics.get("firestore.googleapis.com/document/write_count", 0)
    deletes = metrics.get("firestore.googleapis.com/document/delete_count", 0)
    storage_bytes = metrics.get("firestore.googleapis.com/storage/total_bytes", 0)
    storage_gib = storage_bytes / (1024**3)

    # Free tiers
    free_reads = 50_000 * days
    free_writes = 20_000 * days
    free_deletes = 20_000 * days
    free_storage_gib = 1.0

    # Billable amounts
    billable_reads = max(0, reads - free_reads)
    billable_writes = max(0, writes - free_writes)
    billable_deletes = max(0, deletes - free_deletes)
    billable_storage = max(0, storage_gib - free_storage_gib)

    # Costs
    read_cost = (billable_reads / 100_000) * 0.06
    write_cost = (billable_writes / 100_000) * 0.18
    delete_cost = (billable_deletes / 100_000) * 0.02
    storage_cost = billable_storage * 0.18

    total = read_cost + write_cost + delete_cost + storage_cost

    # Free tier savings (what you would have paid)
    free_savings = (
        (min(reads, free_reads) / 100_000) * 0.06
        + (min(writes, free_writes) / 100_000) * 0.18
        + (min(deletes, free_deletes) / 100_000) * 0.02
        + min(storage_gib, free_storage_gib) * 0.18
    )

    return CostBreakdown(
        service="firestore",
        total_cost=round(total, 2),
        components={
            "reads": round(read_cost, 2),
            "writes": round(write_cost, 2),
            "deletes": round(delete_cost, 2),
            "storage": round(storage_cost, 2),
        },
        free_tier_savings=round(free_savings, 2),
        billable_usage={
            "reads": int(billable_reads),
            "writes": int(billable_writes),
            "deletes": int(billable_deletes),
            "storage_gib": round(billable_storage, 2),
        },
        pricing_notes=[
            f"Total reads: {reads:,} ({billable_reads:,} billable after {free_reads:,} free)",
            f"Total writes: {writes:,} ({billable_writes:,} billable after {free_writes:,} free)",
            f"Total deletes: {deletes:,} ({billable_deletes:,} billable after {free_deletes:,} free)",
            f"Storage: {storage_gib:.2f} GiB ({billable_storage:.2f} GiB billable after {free_storage_gib} GiB free)",
        ],
    )


def calculate_rtdb_costs(metrics: Dict, days: int) -> CostBreakdown:
    """
    Calculate Firebase Realtime Database costs.

    Free tier (Spark plan):
    - 1 GB storage
    - 10 GB bandwidth

    Pricing (Blaze plan):
    - $5 per GB storage/month
    - $1 per GB bandwidth
    """
    storage_bytes = metrics.get("firebasedatabase.googleapis.com/storage/total_bytes", 0)
    bandwidth_bytes = metrics.get("firebasedatabase.googleapis.com/network/monthly_sent", 0)
    api_hits = metrics.get("firebasedatabase.googleapis.com/network/api_hits_count", 0)

    storage_gb = storage_bytes / (1024**3)
    bandwidth_gb = bandwidth_bytes / (1024**3)

    # Free tiers (assuming Blaze plan)
    free_storage_gb = 1.0
    free_bandwidth_gb = 10.0

    # Billable amounts
    billable_storage = max(0, storage_gb - free_storage_gb)
    billable_bandwidth = max(0, bandwidth_gb - free_bandwidth_gb)

    # Costs
    storage_cost = billable_storage * 5.00
    bandwidth_cost = billable_bandwidth * 1.00

    total = storage_cost + bandwidth_cost

    # Free tier savings
    free_savings = min(storage_gb, free_storage_gb) * 5.00 + min(
        bandwidth_gb, free_bandwidth_gb
    ) * 1.00

    return CostBreakdown(
        service="rtdb",
        total_cost=round(total, 2),
        components={
            "storage": round(storage_cost, 2),
            "bandwidth": round(bandwidth_cost, 2),
        },
        free_tier_savings=round(free_savings, 2),
        billable_usage={
            "storage_gb": round(billable_storage, 2),
            "bandwidth_gb": round(billable_bandwidth, 2),
            "api_hits": int(api_hits),
        },
        pricing_notes=[
            f"Storage: {storage_gb:.2f} GB ({billable_storage:.2f} GB billable after {free_storage_gb} GB free)",
            f"Bandwidth: {bandwidth_gb:.2f} GB ({billable_bandwidth:.2f} GB billable after {free_bandwidth_gb} GB free)",
            f"API hits: {api_hits:,} (included in bandwidth cost)",
        ],
    )


def calculate_functions_costs(metrics: Dict, days: int) -> CostBreakdown:
    """
    Calculate Cloud Functions costs (approximate).

    Note: Actual costs depend on memory, CPU time, and network egress.
    This provides a rough estimate based on execution count.
    """
    executions = metrics.get("cloudfunctions.googleapis.com/function/execution_count", 0)

    # Rough estimate: $0.40 per million invocations + compute time
    # This is a simplified calculation
    invocation_cost = (executions / 1_000_000) * 0.40

    # Note: This doesn't include compute time, which varies by function
    # configuration. Would need more detailed metrics.

    return CostBreakdown(
        service="functions",
        total_cost=round(invocation_cost, 2),
        components={
            "invocations": round(invocation_cost, 2),
        },
        free_tier_savings=0.0,  # First 2M invocations free
        billable_usage={
            "executions": int(executions),
        },
        pricing_notes=[
            f"Executions: {executions:,}",
            "WARNING: This is approximate. Actual costs depend on:",
            "  - Memory allocation",
            "  - CPU time",
            "  - Network egress",
            "  - Always-on instances (minInstances > 0)",
            "Check Cloud Functions billing for exact breakdown.",
        ],
    )


def calculate_bigquery_costs(metrics: Dict, days: int) -> CostBreakdown:
    """Calculate BigQuery costs."""
    stored_bytes = metrics.get("bigquery.googleapis.com/storage/stored_bytes", 0)
    query_count = metrics.get("bigquery.googleapis.com/query/count", 0)
    scanned_bytes = metrics.get("bigquery.googleapis.com/query/scanned_bytes", 0)

    stored_tb = stored_bytes / (1024**4)
    scanned_tb = scanned_bytes / (1024**4)

    # Active storage: $0.02 per GB ($20 per TB)
    # Long-term storage (90+ days): $0.01 per GB ($10 per TB)
    # Assuming active storage
    storage_cost = stored_tb * 1024 * 0.02

    # Query: $5 per TB scanned
    query_cost = scanned_tb * 5.00

    total = storage_cost + query_cost

    return CostBreakdown(
        service="bigquery",
        total_cost=round(total, 2),
        components={
            "storage": round(storage_cost, 2),
            "queries": round(query_cost, 2),
        },
        free_tier_savings=0.0,  # First 10GB queries/month free
        billable_usage={
            "stored_tb": round(stored_tb, 3),
            "scanned_tb": round(scanned_tb, 3),
            "query_count": int(query_count),
        },
        pricing_notes=[
            f"Storage: {stored_tb:.3f} TB",
            f"Queries: {query_count:,} queries scanning {scanned_tb:.3f} TB",
            "First 10 GB of queries per month are free",
        ],
    )


def main():
    if len(sys.argv) != 3:
        print("Usage: calculate_costs.py <metrics.json> <days_in_month>", file=sys.stderr)
        sys.exit(1)

    metrics_file = sys.argv[1]
    days = int(sys.argv[2])

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

    # Calculate costs based on service
    if service == "firestore":
        breakdown = calculate_firestore_costs(metrics, days)
    elif service in ["rtdb", "realtime-db", "firebase-db"]:
        breakdown = calculate_rtdb_costs(metrics, days)
    elif service in ["functions", "cloud-functions"]:
        breakdown = calculate_functions_costs(metrics, days)
    elif service == "bigquery":
        breakdown = calculate_bigquery_costs(metrics, days)
    else:
        print(f"ERROR: Cost calculation not implemented for service: {service}", file=sys.stderr)
        sys.exit(1)

    # Output result
    result = asdict(breakdown)
    result["calculation_date"] = data.get("collection_time", "unknown")
    result["days_in_period"] = days

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
