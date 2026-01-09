# GCP Cost Optimization Patterns

Anti-patterns identified from real-world cost analysis, with detection criteria, root causes, fixes, and expected impact.

## Pattern 1: Database Over-Reading

### Detection Criteria
- **Read/Write Ratio > 50:1** (Case Study case: 240:1)
- Continuous high read rate (constant reads/second)
- Read operations significantly exceed write operations
- Same data fetched repeatedly

### Root Causes
1. **No Client-Side Caching** - Every page load fetches from database
2. **Missing Pagination** - Fetching entire collections unnecessarily
3. **Unbounded Queries** - No `.limit()` on queries
4. **Zombie Listeners** - Real-time listeners not cleaned up
5. **No Offline Persistence** - Firestore offline mode disabled

### Case Study Example
- **Observed**: 69,852,686 reads/month with only 291,183 writes
- **Ratio**: 240:1 (reading same data 240 times per write!)
- **Rate**: 26 reads/second continuously, 24/7
- **Cost Impact**: $40.98/month just for reads

### Fixes

#### Fix 1: Add Pagination
```javascript
// BEFORE: Unbounded query (fetches everything)
const workouts = await firebase.firestore()
  .collection('workouts')
  .orderBy('date', 'desc')
  .get()

// AFTER: Paginated query
const workouts = await firebase.firestore()
  .collection('workouts')
  .orderBy('date', 'desc')
  .limit(30)  // Only fetch what's needed
  .get()

// For pagination:
const nextPage = await firebase.firestore()
  .collection('workouts')
  .orderBy('date', 'desc')
  .startAfter(lastVisible)
  .limit(30)
  .get()
```

**Expected Impact**: 70-90% reduction in reads

#### Fix 2: Enable Offline Persistence
```javascript
// Enable Firestore offline caching
firebase.firestore().enablePersistence({
  synchronizeTabs: true
}).catch((err) => {
  if (err.code == 'failed-precondition') {
    // Multiple tabs open, persistence can only be enabled in one tab
  } else if (err.code == 'unimplemented') {
    // Browser doesn't support persistence
  }
})
```

**Expected Impact**: 50-70% reduction in reads (data cached locally)

#### Fix 3: Use Snapshot Listeners Efficiently
```javascript
// BEFORE: Fetch entire collection every time
const listener = firebase.firestore()
  .collection('users')
  .onSnapshot(snapshot => {
    // Processes all documents
    snapshot.docs.forEach(doc => {
      updateUI(doc.data())
    })
  })

// AFTER: Only process changes
const listener = firebase.firestore()
  .collection('users')
  .onSnapshot(snapshot => {
    // Only process changes
    snapshot.docChanges().forEach(change => {
      if (change.type === 'added') {
        addToUI(change.doc.data())
      } else if (change.type === 'modified') {
        updateUI(change.doc.data())
      } else if (change.type === 'removed') {
        removeFromUI(change.doc.data())
      }
    })
  })

// CRITICAL: Clean up listener when done
componentWillUnmount() {
  listener()  // Unsubscribe
}
```

**Expected Impact**: 30-50% reduction in reads

### Total Expected Savings
**Cost Reduction**: 70-90% of read costs ($28-36/month for Case Study)
**Implementation Time**: 2-4 hours
**Risk**: Low (changes are reversible)

---

## Pattern 2: Cloud Functions Always-On

### Detection Criteria
- **minInstances = 1** on low-traffic functions
- Function idle >95% of the time
- Invocations < 1000/day but paying for 24/7 uptime
- Cost ~$10/month per function just to stay warm

### Root Causes
1. **Unnecessary Warm Instances** - Set minInstances=1 to avoid cold starts but traffic doesn't justify it
2. **Copy-Paste Configuration** - Applied same config to all functions
3. **Over-Optimization** - Optimized for latency at expense of cost

### Case Study Example
- **Observed**: 12 functions all with minInstances=1
- **Invocations**: ~4,300/month total (143/day, 6/hour)
- **Idle Time**: >99%
- **Cost Impact**: $115.44/month for mostly idle instances

### Fixes

#### Fix 1: Set minInstances=0 for Low-Traffic Functions
```bash
# For Gen1 Functions (via Firebase)
# Edit firebase.json:
{
  "functions": {
    "source": "functions",
    "runtime": "nodejs18"
  }
}

# In functions/index.js:
exports.myFunction = functions
  .runWith({
    minInstances: 0  // Let it scale to zero
  })
  .https.onRequest((req, res) => {
    // Function code
  })

# Deploy
firebase deploy --only functions
```

```bash
# For Gen2 Functions (Cloud Run)
gcloud run services update my-function \
  --region=us-central1 \
  --min-instances=0 \
  --project=my-project
```

**Expected Impact**: 85-95% cost reduction per function

#### Fix 2: Keep minInstances=1 Only for Critical Functions
Reserve always-on instances for:
- User-facing API endpoints with strict latency requirements
- Functions called >1000 times/day
- Functions where 1-2 second cold start is unacceptable

### Total Expected Savings
**Cost Reduction**: $100-105/month (Case Study: 11 of 12 functions to minInstances=0)
**Implementation Time**: 30 minutes
**Risk**: Low (users may see 1-2 second delay on first invocation)

---

## Pattern 3: Realtime Database Over-Downloading

### Detection Criteria
- **Bandwidth > Storage Size** - Downloading more than total database size
- Large payload sizes (GB of downloads from MB of storage)
- High bandwidth relative to API operations
- Missing query limits (`.limitToLast()`)

### Case Study Example
- **Observed**: 69 GB downloads from 14 GB storage
- **Ratio**: 4.9× (downloading entire database 5 times per month!)
- **API Operations**: 7.9M total
- **Cost Impact**: $69.14/month for bandwidth alone

### Fixes

#### Fix 1: Add Query Limits
```javascript
// BEFORE: Fetch entire node
firebase.database().ref('users/' + uid + '/workouts')
  .once('value')
  .then(snapshot => {
    const workouts = snapshot.val()
    // Process all workouts
  })

// AFTER: Limit query
firebase.database().ref('users/' + uid + '/workouts')
  .orderByChild('date')
  .limitToLast(30)  // Only last 30 workouts
  .once('value')
  .then(snapshot => {
    const workouts = snapshot.val()
    // Process only needed data
  })
```

**Expected Impact**: 60-80% bandwidth reduction

#### Fix 2: Enable Offline Persistence
```javascript
// Enable offline mode for Realtime Database
firebase.database().ref('.info/connected').on('value', (snapshot) => {
  if (snapshot.val() === true) {
    console.log('Connected')
  } else {
    console.log('Offline - using cached data')
  }
})

// Data automatically cached locally
// Subsequent reads served from cache
```

**Expected Impact**: 50-70% bandwidth reduction

### Total Expected Savings
**Cost Reduction**: $40-55/month (Case Study: 69 GB → 15 GB)
**Implementation Time**: 2-3 hours
**Risk**: Low (no user-facing changes)

---

## Pattern 4: BigQuery Table Sprawl

### Detection Criteria
- Large number of small tables (>100 tables with <1 GB each)
- High storage cost relative to query cost
- Tables not partitioned by date
- No table expiration policies

### Root Causes
1. **No Data Lifecycle** - Tables created but never deleted
2. **Poor Partitioning** - Daily tables instead of partitioned tables
3. **Logging Overuse** - Streaming logs to BigQuery without limits

### Fixes

#### Fix 1: Consolidate to Partitioned Tables
```sql
-- Create partitioned table
CREATE TABLE `project.dataset.events`
PARTITION BY DATE(timestamp)
OPTIONS(
  partition_expiration_days=90
)
AS SELECT * FROM `project.dataset.events_*`

-- Drop old tables
DROP TABLE `project.dataset.events_20250101`
-- ... repeat for each table
```

#### Fix 2: Set Table Expiration
```bash
# Set expiration on tables
bq update --expiration 7776000 project:dataset.temp_table  # 90 days
```

**Expected Impact**: 40-60% storage cost reduction

---

## Pattern 5: Cloud Storage Inefficient Classes

### Detection Criteria
- Standard storage class for rarely accessed data
- No lifecycle policies defined
- Objects >30 days old still in Standard class
- High storage costs relative to access frequency

### Fixes

#### Fix 1: Set Lifecycle Policies
```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {"age": 30}
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
        "condition": {"age": 90}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"age": 365}
      }
    ]
  }
}
```

```bash
# Apply lifecycle policy
gsutil lifecycle set lifecycle.json gs://bucket-name
```

**Expected Impact**: 30-50% storage cost reduction

---

## Detection Checklist

Use this checklist during analysis:

### Firestore/RTDB
- [ ] Read/Write ratio > 50:1?
- [ ] Continuous read rate (reads/second never drops to zero)?
- [ ] Storage growing but reads growing faster?
- [ ] Queries without `.limit()`?
- [ ] Offline persistence disabled?

### Cloud Functions
- [ ] minInstances > 0 on functions?
- [ ] Invocations < 1000/day per function?
- [ ] Cost > $10/month per function?
- [ ] Similar cost across all functions (suggests misconfiguration)?

### Realtime Database
- [ ] Bandwidth > storage size?
- [ ] Large payloads (MB+ per query)?
- [ ] No query limits (`.limitToLast()`)?
- [ ] High downloads/operations ratio?

### BigQuery
- [ ] >50 tables in dataset?
- [ ] Tables without expiration?
- [ ] Non-partitioned event tables?
- [ ] Storage cost > query cost?

### Cloud Storage
- [ ] All objects in Standard class?
- [ ] No lifecycle policies?
- [ ] Objects >90 days old?
- [ ] Rarely accessed data (access < 1/month)?

---

## Quick Wins Summary

| Pattern | Detection | Fix Time | Savings | Risk |
|---------|-----------|----------|---------|------|
| Database Over-Reading | Read/Write > 50:1 | 2-4h | 70-90% | Low |
| Functions Always-On | minInstances=1 | 30min | 85-95% | Low |
| RTDB Over-Downloading | Bandwidth > Storage | 2-3h | 60-80% | Low |
| BigQuery Sprawl | >100 tables | 1-2h | 40-60% | Medium |
| Storage Class | No lifecycle | 1h | 30-50% | Low |

**Total Potential Savings from All Patterns**: 60-75% of monthly costs

---

## Verification After Fixes

After implementing fixes, verify impact:

```bash
# Wait 7 days, then re-run analysis
./fetch_metrics.sh my-project firestore <start> <end>

# Compare metrics:
# - Reads should be 70-90% lower
# - Costs should match reduction
# - No increase in errors/latency
```

Monitor for 2 weeks to ensure:
1. Costs dropped as expected
2. No user complaints about performance
3. Error rates unchanged
4. Application still functions correctly

---

## Sources

Patterns derived from:
- Case Study GCP cost analysis (January 2026)
- 69.8M Firestore reads/month reduced to <10M
- $382/month reduced to $140/month (63% savings)
- 4 hours implementation time
