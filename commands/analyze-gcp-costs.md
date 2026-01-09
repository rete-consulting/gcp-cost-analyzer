---
description: Complete GCP billing analysis with verified data and actionable recommendations
argument-hint: <project-id> [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--output path]
allowed-tools: [Bash, Read, TodoWrite]
model: sonnet
---

# GCP Cost Analysis Command

Analyze Google Cloud Platform billing to identify cost drivers and optimization opportunities using verified metrics.

## Arguments

Parse arguments from $ARGUMENTS:
- **project_id** (required): GCP project ID
- **--start** (optional): Start date (YYYY-MM-DD), defaults to first day of previous month
- **--end** (optional): End date (YYYY-MM-DD), defaults to last day of previous month
- **--output** (optional): Report output path, defaults to `./gcp-cost-analysis-{date}.md`

## Critical Principles

**ZERO-ASSUMPTION PHILOSOPHY:**
- Never estimate or guess
- Always query actual metrics
- Use complete date ranges
- Verify data completeness
- Stop if validation fails

This prevents common cost analysis mistakes:
- ❌ Made assumptions → got costs wrong by 100%
- ❌ Used partial data → missed 80% of problem
- ❌ Speculated about issues → wrong root cause
- ✅ Queried Cloud Monitoring API → found real usage
- ✅ Used full month ranges → accurate costs

## Workflow

### Phase 1: Prerequisites Validation (CRITICAL)

**Never skip this phase. Stop before making assumptions.**

```bash
# Run prerequisites check
${CLAUDE_PLUGIN_ROOT}/scripts/check_prerequisites.sh <project_id>
```

If this fails:
- STOP immediately
- Report specific issue to user
- DO NOT proceed with analysis
- DO NOT make assumptions about what might work

**Success criteria:**
- gcloud CLI installed and authenticated
- Project exists and accessible
- Required APIs enabled
- Billing account linked

Create todo list for analysis phases:
```
1. Prerequisites validation
2. Billing discovery
3. Metrics collection for {N} services
4. Cost calculations
5. Pattern analysis
6. Report generation
7. Validation summary
```

### Phase 2: Billing Discovery

**Goal: Identify which services have actual charges (no guessing)**

Query billing data to find services with charges:

```bash
# Get billing account
gcloud billing accounts list --project=<project_id>

# Note: Detailed billing requires BigQuery export or Cloud Console
# For this analysis, we'll focus on known high-cost services:
# - Firestore (billed as "App Engine" - F17B-412E-CB64)
# - Firebase Realtime Database
# - Cloud Functions (Gen1 and Gen2)
# - BigQuery
# - Cloud Storage
```

**Services to analyze** (in priority order):
1. **Firestore** - Check for over-reading (read/write ratio >50:1)
2. **Realtime Database** - Check for over-downloading (bandwidth > storage)
3. **Cloud Functions** - Check for always-on (minInstances > 0)
4. **BigQuery** - Check for table sprawl
5. **Cloud Storage** - Check for inefficient storage classes

Update todos with service-specific tasks.

### Phase 3: Metrics Collection (PARALLEL - NO ASSUMPTIONS)

**CRITICAL: For each service, fetch ACTUAL metrics from Cloud Monitoring API**

For each service to analyze:

```bash
# Fetch metrics using the verified script
METRICS_FILE=$(${CLAUDE_PLUGIN_ROOT}/scripts/fetch_metrics.sh \
  <project_id> \
  <service> \
  <start_date_iso8601> \
  <end_date_iso8601>)

# IMMEDIATELY validate data completeness
${CLAUDE_PLUGIN_ROOT}/scripts/validate_data.py "$METRICS_FILE"

# If validation fails:
if [ $? -ne 0 ]; then
  echo "ERROR: Incomplete data for <service>"
  echo "Cannot proceed with cost calculation"
  echo "Missing or null metrics prevent accurate analysis"
  exit 1
fi
```

**Date format:** ISO 8601 with timezone
- Start: `YYYY-MM-DDT00:00:00Z`
- End: `YYYY-MM-DDT23:59:59Z`
- Example: `2025-12-01T00:00:00Z` to `2025-12-31T23:59:59Z`

**Services and their metrics:**

**Firestore:**
- `firestore.googleapis.com/document/read_count`
- `firestore.googleapis.com/document/write_count`
- `firestore.googleapis.com/document/delete_count`
- `firestore.googleapis.com/storage/total_bytes`

**Realtime Database:**
- `firebasedatabase.googleapis.com/network/monthly_sent`
- `firebasedatabase.googleapis.com/storage/total_bytes`
- `firebasedatabase.googleapis.com/network/api_hits_count`

**Cloud Functions:**
- `cloudfunctions.googleapis.com/function/execution_count`
- `cloudfunctions.googleapis.com/function/execution_times`
- `cloudfunctions.googleapis.com/function/active_instances`

Run these in parallel for efficiency, but validate each before proceeding.

Mark each service as collected in todos.

### Phase 4: Cost Calculation (WITH FREE TIER ACCOUNTING)

**CRITICAL: Use exact pricing formulas, account for free tiers**

For each service with collected metrics:

```bash
# Calculate costs
DAYS_IN_MONTH=<calculate from date range>

${CLAUDE_PLUGIN_ROOT}/scripts/calculate_costs.py \
  "$METRICS_FILE" \
  $DAYS_IN_MONTH > "costs-<service>.json"
```

**Verification required:**
- If user provided actual billing costs, compare calculated vs actual
- Flag discrepancies > 5%
- Document any differences
- DO NOT assume calculated is wrong if it differs - investigate

**Example verification:**
```
Calculated: $124.84
Reported: $124.24
Difference: $0.60 (0.5%)
Status: ✓ MATCH (within tolerance)
```

Mark each calculation complete in todos.

### Phase 5: Pattern Analysis

**Goal: Identify specific anti-patterns, not generic advice**

For each service, check against known patterns from `references/cost-optimization-patterns.md`:

**Firestore checks:**
```python
# Calculate read/write ratio
reads = metrics["firestore.googleapis.com/document/read_count"]
writes = metrics["firestore.googleapis.com/document/write_count"]
ratio = reads / writes if writes > 0 else 0

if ratio > 50:
    print(f"PATTERN DETECTED: Database Over-Reading")
    print(f"Read/Write Ratio: {ratio}:1 (healthy is <10:1)")
    print(f"Root cause: No pagination, no caching, or zombie listeners")
    print(f"Expected savings: 70-90% of read costs")
    print(f"See: examples/firestore-analysis.md")
```

**Realtime Database checks:**
```python
# Calculate bandwidth vs storage ratio
bandwidth_bytes = metrics["firebasedatabase.googleapis.com/network/monthly_sent"]
storage_bytes = metrics["firebasedatabase.googleapis.com/storage/total_bytes"]

bandwidth_gb = bandwidth_bytes / (1024**3)
storage_gb = storage_bytes / (1024**3)
ratio = bandwidth_gb / storage_gb if storage_gb > 0 else 0

if ratio > 2:
    print(f"PATTERN DETECTED: RTDB Over-Downloading")
    print(f"Bandwidth/Storage Ratio: {ratio:.1f}× (downloading {ratio:.1f}× database size)")
    print(f"Root cause: Missing query limits, no offline mode")
    print(f"Expected savings: 60-80% of bandwidth costs")
```

**Cloud Functions checks:**
```bash
# Check for minInstances > 0
gcloud functions list --project=<project_id> --format=json | \
  jq '.[] | select(.minInstances > 0) | {name, minInstances, invocations}'

# If functions with minInstances=1 and low invocations:
if invocations_per_day < 1000; then
    print("PATTERN DETECTED: Functions Always-On")
    print("Fix: Set minInstances=0 for low-traffic functions")
    print("Expected savings: 85-95% per function")
fi
```

Only report patterns that have supporting data. DO NOT speculate.

### Phase 6: Report Generation

**Build structured markdown report with:**

#### Section 1: Executive Summary
- Total monthly cost
- Top 3 cost drivers
- Total potential savings
- Implementation effort

#### Section 2: Verified Usage Data
For each service:
- Actual metrics (with source: "Cloud Monitoring API")
- Date range (full month)
- Collection timestamp
- Data completeness: 100%

Example:
```markdown
## Firestore Usage (December 2025)

**Source**: Cloud Monitoring API
**Date Range**: 2025-12-01 to 2025-12-31 (31 days, FULL MONTH)
**Data Completeness**: 100%

- **Reads**: 69,852,686 operations (2.25M/day, 26/second)
- **Writes**: 291,183 operations (9.4K/day)
- **Deletes**: 15,218 operations
- **Storage**: 466.88 GiB
- **Read/Write Ratio**: 240:1 ⚠️
```

#### Section 3: Cost Breakdown
For each service:
- Total cost
- Component breakdown
- Free tier savings
- Billable usage

Example:
```markdown
## Firestore Costs

**Total**: $124.84/month

| Component | Usage | Free Tier | Billable | Unit Cost | Total |
|-----------|-------|-----------|----------|-----------|-------|
| Reads | 69.8M | 1.55M | 68.3M | $0.06/100K | $40.98 |
| Writes | 291K | 620K | 0 | $0.18/100K | $0.00 |
| Deletes | 15K | 620K | 0 | $0.02/100K | $0.00 |
| Storage | 466.88 GiB | 1 GiB | 465.88 GiB | $0.18/GiB | $83.86 |

**Free Tier Savings**: $0.09/month (what you would have paid)

**Verification**: Calculated $124.84 vs Reported $124.24 = ✓ Match (±$0.60)
```

#### Section 4: Root Cause Analysis
For each detected pattern:
- Pattern name
- Detection criteria (what triggered it)
- Actual metrics proving it
- Root cause explanation
- References to examples

#### Section 5: Recommendations
Priority-ranked with:
- Specific code fixes (from examples/)
- Implementation steps
- Expected savings (quantified)
- Implementation time
- Risk assessment

Example:
```markdown
### Priority 1: Firestore Over-Reading → Save $90/month

**Root Cause**: 240:1 read/write ratio from:
1. No pagination (fetching all 10K workouts every load)
2. No offline persistence (no caching)
3. Zombie listeners (not cleaned up)

**Fixes**:

1. Add pagination (1.5 hours):
   \`\`\`javascript
   // Before
   .collection('workouts').get()

   // After
   .collection('workouts').limit(30).get()
   \`\`\`
   **Impact**: -70% reads

2. Enable offline persistence (30 min):
   \`\`\`javascript
   firebase.firestore().enablePersistence()
   \`\`\`
   **Impact**: -50% reads (cached locally)

3. Clean up listeners (1 hour):
   \`\`\`javascript
   useEffect(() => {
     const unsubscribe = firestore()...
     return () => unsubscribe() // CRITICAL
   }, [])
   \`\`\`
   **Impact**: Stop zombie reads

**Total Expected Savings**: $90-100/month
**Implementation Time**: 3 hours
**Risk**: Low (reversible)
**See**: examples/firestore-analysis.md
```

#### Section 6: Implementation Plan
Timeline with checkboxes:
```markdown
## Implementation Plan

### Phase 1: Quick Wins (Today, 2 hours, $120/month savings)
- [ ] Set Cloud Functions minInstances=0 (30 min) → Save $105/month
- [ ] Enable Firestore offline persistence (30 min) → Save $15/month
- [ ] Add pagination to top 5 queries (1 hour) → Save $20/month

### Phase 2: Structural Fixes (This Week, 3 hours, $120/month savings)
- [ ] Add .limit() to all Firestore queries (2 hours) → Save $80/month
- [ ] Add .limitToLast() to RTDB queries (1 hour) → Save $40/month

### Phase 3: Monitoring (Ongoing)
- [ ] Wait 7 days after Phase 1
- [ ] Re-run analysis: /analyze-gcp-costs <project> --start YYYY-MM-DD --end YYYY-MM-DD
- [ ] Verify expected savings
- [ ] Adjust if needed

**Total Expected Savings**: $240/month (63% reduction)
**Total Implementation**: 5 hours
**ROI**: $48/hour
```

### Phase 7: Validation Summary

**CRITICAL: Document what was checked and verified**

```markdown
## Analysis Validation

### Metrics Checked: ✓
- Firestore: 4 metrics (100% complete)
- Realtime DB: 3 metrics (100% complete)
- Cloud Functions: 3 metrics (100% complete)

### Assumptions Made: 0 (ZERO)
All data sourced from Cloud Monitoring API. No estimates or guesses.

### Data Quality:
- Date Range: Complete calendar month (31 days)
- Completeness: 100%
- Verification: Costs match billing API ±2%

### Confidence Level: HIGH
All recommendations based on verified patterns with supporting data.
```

Output report to specified path or default location.

## Error Handling

### Prerequisites Failure
```
ERROR: Prerequisites check failed

Issue: <specific problem>
Fix: <specific command to resolve>

Cannot proceed with analysis. Please resolve issue and try again.
```

### Incomplete Metrics
```
ERROR: Incomplete metrics for <service>

Missing metrics:
- <metric 1>
- <metric 2>

Possible causes:
- Service not active in date range
- API permissions insufficient
- Service not enabled

Cannot calculate costs without complete data.
```

### Cost Discrepancy
```
WARNING: Cost calculation discrepancy for <service>

Calculated: $X.XX
Reported: $Y.YY
Difference: $Z.ZZ (P%)

Possible reasons:
- Different billing period
- Additional fees not in metrics
- Free tier discount applied
- Regional pricing differences

Proceeding with calculated value. Review billing console for details.
```

## Output

Generate markdown report at specified path with:
- Timestamp
- Project ID
- Date range analyzed
- All sections above
- Footer with re-analysis command

```markdown
---

**Analysis Date**: 2026-01-09
**Project**: your-project-id
**Period**: December 2025 (31 days)
**Tool**: GCP Cost Analyzer v1.0.0

**To re-analyze after fixes:**
\`\`\`
/analyze-gcp-costs your-project-id --start 2026-01-15 --end 2026-01-22
\`\`\`
```

## Example Usage

```bash
# Basic (uses previous month)
/analyze-gcp-costs my-project-123

# Custom date range
/analyze-gcp-costs my-project-123 --start 2025-12-01 --end 2025-12-31

# Custom output path
/analyze-gcp-costs my-project-123 --output ~/reports/gcp-analysis.md
```

## Success Criteria

Analysis is successful when:
- ✓ Prerequisites passed
- ✓ All metrics collected (100% completeness)
- ✓ All costs calculated
- ✓ Costs verified against billing (±5%)
- ✓ Patterns identified with supporting data
- ✓ Recommendations quantified with examples
- ✓ Zero assumptions made
- ✓ Report generated

Report should enable user to:
1. Understand exactly what's expensive (verified data)
2. Know why it's expensive (root causes)
3. Fix it themselves (code examples)
4. Quantify expected savings (specific numbers)
5. Track progress (re-run command after fixes)

## References

- Scripts: `${CLAUDE_PLUGIN_ROOT}/scripts/`
- Patterns: `${CLAUDE_PLUGIN_ROOT}/references/cost-optimization-patterns.md`
- Examples: `${CLAUDE_PLUGIN_ROOT}/examples/`
- Original case: Real-world GCP cost optimization
