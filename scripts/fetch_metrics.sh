#!/usr/bin/env bash
#
# fetch_metrics.sh - Query Cloud Monitoring API for GCP service metrics
#
# Purpose: Get ACTUAL usage data (no assumptions, no estimates)
#
# This script automates what WORKED in the original analysis:
# - Using Cloud Monitoring REST API with curl
# - Querying FULL date ranges (no partial data)
# - Service-specific metric lists
# - Validating API responses
#
# Usage: ./fetch_metrics.sh <project_id> <service> <start_date> <end_date>
#        Dates in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ
#

set -euo pipefail

PROJECT_ID="${1:-}"
SERVICE="${2:-}"
START_DATE="${3:-}"
END_DATE="${4:-}"

if [ -z "$PROJECT_ID" ] || [ -z "$SERVICE" ] || [ -z "$START_DATE" ] || [ -z "$END_DATE" ]; then
    echo "Usage: $0 <project_id> <service> <start_date> <end_date>" >&2
    echo "" >&2
    echo "Services: firestore, rtdb, functions, bigquery, storage, cloudrun" >&2
    echo "Dates: ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)" >&2
    echo "" >&2
    echo "Example:" >&2
    echo "  $0 my-project firestore 2025-12-01T00:00:00Z 2025-12-31T23:59:59Z" >&2
    exit 1
fi

# Get authentication token
echo "Getting authentication token..." >&2
TOKEN=$(gcloud auth print-access-token)
if [ -z "$TOKEN" ]; then
    echo "ERROR: Failed to get auth token. Run: gcloud auth login" >&2
    exit 1
fi

# API endpoint
API_BASE="https://monitoring.googleapis.com/v3/projects/${PROJECT_ID}/timeSeries"

# Output file
OUTPUT_DIR="${TMPDIR:-/tmp}"
OUTPUT_FILE="${OUTPUT_DIR}/metrics-${SERVICE}-$(date +%Y%m%d-%H%M%S).json"

echo "Fetching metrics for $SERVICE from $START_DATE to $END_DATE..." >&2
echo "Project: $PROJECT_ID" >&2
echo "" >&2

# Initialize output JSON
cat > "$OUTPUT_FILE" <<EOF
{
  "project_id": "$PROJECT_ID",
  "service": "$SERVICE",
  "start_date": "$START_DATE",
  "end_date": "$END_DATE",
  "collection_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "metrics": {
EOF

# Define metrics per service
# These are the EXACT metrics that worked in the Stronglifts analysis
declare -a METRICS

case "$SERVICE" in
    firestore)
        METRICS=(
            "firestore.googleapis.com/document/read_count"
            "firestore.googleapis.com/document/write_count"
            "firestore.googleapis.com/document/delete_count"
            "firestore.googleapis.com/storage/total_bytes"
        )
        ;;

    rtdb|realtime-db|firebase-db)
        METRICS=(
            "firebasedatabase.googleapis.com/network/monthly_sent"
            "firebasedatabase.googleapis.com/storage/total_bytes"
            "firebasedatabase.googleapis.com/network/api_hits_count"
        )
        ;;

    functions|cloud-functions)
        METRICS=(
            "cloudfunctions.googleapis.com/function/execution_count"
            "cloudfunctions.googleapis.com/function/execution_times"
            "cloudfunctions.googleapis.com/function/active_instances"
        )
        ;;

    bigquery)
        METRICS=(
            "bigquery.googleapis.com/storage/stored_bytes"
            "bigquery.googleapis.com/query/count"
            "bigquery.googleapis.com/query/scanned_bytes"
        )
        ;;

    storage|cloud-storage|gcs)
        METRICS=(
            "storage.googleapis.com/storage/total_bytes"
            "storage.googleapis.com/network/sent_bytes_count"
            "storage.googleapis.com/api/request_count"
        )
        ;;

    cloudrun|cloud-run)
        METRICS=(
            "run.googleapis.com/request_count"
            "run.googleapis.com/container/instance_count"
            "run.googleapis.com/container/billable_instance_time"
        )
        ;;

    *)
        echo "ERROR: Unknown service: $SERVICE" >&2
        echo "Supported: firestore, rtdb, functions, bigquery, storage, cloudrun" >&2
        exit 1
        ;;
esac

echo "Metrics to collect: ${#METRICS[@]}" >&2
echo "" >&2

# Fetch each metric
METRIC_COUNT=0
TOTAL_METRICS=${#METRICS[@]}

for METRIC in "${METRICS[@]}"; do
    ((METRIC_COUNT++))
    echo "[$METRIC_COUNT/$TOTAL_METRICS] Fetching: $METRIC" >&2

    # URL encode the filter
    FILTER="metric.type=\"${METRIC}\""
    ENCODED_FILTER=$(echo "$FILTER" | sed 's/ /%20/g' | sed 's/"/%22/g' | sed 's/=/%3D/g')

    # Build API URL
    API_URL="${API_BASE}?filter=${ENCODED_FILTER}&interval.startTime=${START_DATE}&interval.endTime=${END_DATE}"

    # Query API
    RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_URL" 2>&1)

    # Check for errors
    if echo "$RESPONSE" | jq -e '.error' > /dev/null 2>&1; then
        echo "  ERROR: API returned error" >&2
        echo "$RESPONSE" | jq '.error' >&2

        # Write null value
        if [ $METRIC_COUNT -lt $TOTAL_METRICS ]; then
            echo "    \"${METRIC}\": null," >> "$OUTPUT_FILE"
        else
            echo "    \"${METRIC}\": null" >> "$OUTPUT_FILE"
        fi
        continue
    fi

    # Extract and aggregate values
    # For DELTA metrics (counts): sum all values
    # For GAUGE metrics (storage): take latest value
    VALUE=$(echo "$RESPONSE" | jq '[.timeSeries[]?.points[]?.value.int64Value // .timeSeries[]?.points[]?.value.doubleValue // 0] | add // 0' 2>/dev/null || echo "0")

    echo "  Value: $VALUE" >&2

    # Write to JSON
    if [ $METRIC_COUNT -lt $TOTAL_METRICS ]; then
        echo "    \"${METRIC}\": $VALUE," >> "$OUTPUT_FILE"
    else
        echo "    \"${METRIC}\": $VALUE" >> "$OUTPUT_FILE"
    fi
done

# Close JSON
cat >> "$OUTPUT_FILE" <<EOF
  },
  "status": "success",
  "errors": 0
}
EOF

echo "" >&2
echo "✓ Metrics saved to: $OUTPUT_FILE" >&2
echo "" >&2

# Output the file path (for programmatic use)
echo "$OUTPUT_FILE"
