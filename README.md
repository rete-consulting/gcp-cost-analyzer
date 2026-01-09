# GCP Cost Analyzer for Claude Code

Stop paying for waste. Get actionable GCP cost optimizations in minutes.

## What This Does

Analyzes your GCP project and tells you:
- **What's expensive** (verified data, no guessing)
- **Why it's expensive** (root cause analysis)
- **How to fix it** (specific code examples)
- **How much you'll save** (quantified impact)

Based on real debugging session that reduced costs 64% ($382 → $140/month).

## Quick Start

### Prerequisites
- Claude Code installed
- gcloud CLI authenticated (`gcloud auth login`)
- GCP project with billing enabled

### Installation

```bash
# Plugin should be in ~/.claude/plugins/gcp-cost-analyzer/
# Claude Code auto-discovers plugins on startup
```

### Basic Usage

```bash
# In Claude Code
/analyze-gcp-costs your-project-id

# Or with custom date range
/analyze-gcp-costs your-project-id --start 2025-12-01 --end 2025-12-31

# Quick metrics check
/fetch-gcp-metrics your-project-id firestore --start 2026-01-01 --end 2026-01-07
```

Wait ~5 minutes, get comprehensive report.

## What Makes This Different

### Other tools:
- Show you billing graphs
- Give generic advice
- Leave you to figure out root causes

### This tool:
- Queries actual usage metrics via Cloud Monitoring API
- Identifies specific anti-patterns (over-reading, always-on functions, etc.)
- Provides exact code fixes with before/after examples
- Calculates expected savings per fix

## Lessons from Real Debugging

This tool was designed based on actual GCP debugging where we:
- ❌ Made assumptions → got costs wrong by 100%
- ❌ Used partial data → missed 80% of the problem
- ❌ Guessed at issues → wrong root cause
- ✅ Queried Cloud Monitoring API → found real usage
- ✅ Used full month ranges → accurate costs
- ✅ Calculated with free tiers → matched billing exactly
- ✅ Identified patterns → 64% cost reduction

This tool automates what worked, prevents what didn't.

## Supported Services

- ✅ **Cloud Firestore** - Catches over-reading, missing caching, unbounded queries
- ✅ **Firebase Realtime Database** - Bandwidth optimization, query limits
- ✅ **Cloud Functions (Gen1 & Gen2)** - minInstances issues, cold start optimization
- ✅ **Cloud Run** - Scaling configuration, always-on detection
- ✅ **BigQuery** - Storage/query optimization patterns
- ✅ **Cloud Storage** - Lifecycle policies, storage class optimization
- 🔄 More services coming...

## Example Results

### Before:
```
Firestore: $125/month (~70M reads, 240:1 read/write ratio)
Functions: $115/month (12 always-on with minInstances=1)
Realtime DB: $125/month (~70 GB downloads)
Total: $365/month
```

### After (4 hours of fixes):
```
Firestore: $35/month (~5M reads, added pagination + caching)
Functions: $10/month (set minInstances=0 except critical)
Realtime DB: $45/month (added query limits, enabled offline)
Total: $90/month
Savings: $275/month (75%)
ROI: $825/year for 4 hours of work
```

## Commands

- **`/analyze-gcp-costs`** - Full project analysis (recommended)
- **`/fetch-gcp-metrics`** - Quick metrics check for specific service
- **`/optimize-service`** - Deep-dive single service (coming soon)

## What Gets Analyzed

The analysis covers:

1. **Prerequisites Validation** - Ensures gcloud auth, project access, API enablement
2. **Billing Discovery** - Identifies all billable services and top cost drivers
3. **Metrics Collection** - Queries Cloud Monitoring API for actual usage (full date range)
4. **Cost Calculation** - Applies pricing formulas with free tier accounting
5. **Pattern Analysis** - Identifies known anti-patterns (over-reading, always-on, etc.)
6. **Recommendations** - Generates actionable fixes with code examples and savings estimates

## Anti-Patterns Detected

### Database Over-Reading
- **Detection**: Read/Write ratio > 50:1, constant read rate
- **Root Cause**: No caching, missing pagination, zombie listeners
- **Fix**: Add `.limit()`, enable offline persistence, clean up listeners
- **Savings**: 70-90% of read costs

### Cloud Functions Always-On
- **Detection**: minInstances=1 on low-traffic functions
- **Root Cause**: Unnecessary warm instances for infrequent events
- **Fix**: Set minInstances=0 for non-critical functions
- **Savings**: 85-95% of function costs

### Missing Pagination
- **Detection**: Unbounded queries, large payload sizes
- **Root Cause**: Fetching entire collections unnecessarily
- **Fix**: Add pagination with `.limit()` and `.startAfter()`
- **Savings**: 60-80% of bandwidth/read costs

### No Offline Persistence
- **Detection**: High repeat reads for same data
- **Root Cause**: No client-side caching enabled
- **Fix**: Enable Firestore offline persistence
- **Savings**: 50-70% of read costs

[See full pattern catalog in `references/cost-optimization-patterns.md`]

## Examples

See `examples/` directory for complete case studies:
- **firestore-analysis.md** - Firestore over-reading case study
- **cloud-functions-analysis.md** - Always-on functions optimization
- **realtime-db-analysis.md** - Bandwidth reduction strategies
- **sample-report.md** - Annotated report template

## File Structure

```
gcp-cost-analyzer/
├── commands/          # Slash commands
├── agents/            # Autonomous task handlers
├── scripts/           # Automation (bash, python)
├── references/        # Knowledge base (services, pricing, patterns)
└── examples/          # Real case studies
```

## How It Works

1. **Validates prerequisites** - Stops before making assumptions
2. **Queries Cloud Monitoring API** - Gets actual usage (no estimates)
3. **Calculates costs** - Applies pricing formulas with free tiers
4. **Identifies patterns** - Matches against anti-pattern catalog
5. **Generates report** - Provides specific fixes with code examples

## Troubleshooting

### "gcloud not authenticated"
```bash
gcloud auth login
gcloud auth application-default login
```

### "Permission denied on project"
```bash
# Ensure you have these roles:
# - roles/monitoring.viewer
# - roles/cloudfunctions.viewer
# - roles/billing.viewer
```

### "API not enabled"
```bash
gcloud services enable monitoring.googleapis.com --project=YOUR_PROJECT
gcloud services enable cloudfunctions.googleapis.com --project=YOUR_PROJECT
gcloud services enable cloudbilling.googleapis.com --project=YOUR_PROJECT
```

## Contributing

Found a new anti-pattern? Add to `references/cost-optimization-patterns.md`

Support new service? Add to `references/gcp-services-catalog.md`

Improved pricing formula? Update `references/pricing-models.md`

## License

MIT

## Credits

Built from lessons learned in real-world GCP cost optimization projects.

Key learnings: Never assume. Always verify. Query actual metrics. Use full date ranges. Match billing API.
