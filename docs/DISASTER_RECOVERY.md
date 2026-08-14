# Disaster Recovery Plan & Incident Response Runbook

**AI Adaptive Education Platform**  
**Document Version**: 1.0.0  
**Last Updated**: August 14, 2026  
**Target RTO**: < 15 minutes  
**Target RPO**: < 5 minutes  

---

## 1. Executive Summary & Recovery Metrics

This Disaster Recovery (DR) document defines the architectural strategy, automated procedures, backup schedules, and incident response runbooks to ensure business continuity, 100% deterministic data integrity, and strict security isolation during catastrophic failures.

### Key Recovery Objectives (SLAs)

| Service Component | Target RTO (Recovery Time) | Target RPO (Recovery Point) | Backup Frequency | Primary Recovery Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **Relational Database (PostgreSQL/SQLite)** | **< 15 minutes** | **< 5 minutes** | Continuous WAL + Hourly Deltas + Daily Full Dumps | Automated Snapshot Restore & WAL Point-in-Time Recovery (PITR) |
| **Object Storage (PDF & Media Assets)** | **< 10 minutes** | **< 1 hour** | Hourly Sync + Versioning | Cross-Region Replication & Cold Storage Sync |
| **Redis (Cache & Task Queues)** | **< 2 minutes** | **0 minutes (Rebuildable)** | In-Memory / Ephemeral | Automated Session Eviction & DB Queue Rebuilding |
| **Celery Background Workers** | **< 5 minutes** | **0 minutes** | Continuous Monitoring | Worker Auto-Scaling & Dead Letter Queue (DLQ) Re-dispatch |
| **AI Instructor & Model Provider** | **< 30 seconds** | **0 minutes** | Real-Time Health Probes | Automated Multi-Provider Failover (`preferred` $\to$ `fallback`) |

---

## 2. Infrastructure Resilience Architecture

### 2.1 Database Disaster Recovery (Relational Engine)

#### Backup Strategy
1. **Continuous Write-Ahead Logging (WAL)**: All database transactions generate WAL logs shipped asynchronously to secure, encrypted cold storage.
2. **Hourly Delta Snapshots**: Database snapshots taken hourly and stored with SHA-256 integrity checksums.
3. **Daily Full Cold Backups**: Complete database dumps generated daily at 02:00 UTC and retained for 30 days.

#### Restore & Verification Procedure
1. **Restore Execution**:
   - Provision target database node.
   - Extract the latest verified snapshot bundle (`dr_backup_restore.py --action restore`).
   - Replay WAL files up to the target timestamp before incident occurrence.
2. **Verification Checkpoints**:
   - **Schema Integrity**: Confirm 100% table schema parity.
   - **Data Parity**: Verify non-zero counts across `users`, `organizations`, `curricula`, `concepts`, and `student_masteries`.
   - **EWMA Score Verification**: Run deterministic checks on `student_mastery.mastery_score` records to ensure EWMA scores match pre-backup values without corruption.
   - **Audit Trail Validation**: Verify audit log record sequence in `audit_logs` and `mastery_audit_logs`.

---

### 2.2 Object Storage Recovery (S3 / Blob Storage)

#### Storage Strategy
- **Versioning Enabled**: Object versioning is enabled across all curriculum PDF uploads and assessment media buckets to prevent accidental deletion or ransomware overwrites.
- **SHA-256 Content Addressing**: Every uploaded file is stored with its SHA-256 hash digest recorded in the `source_documents` table.

#### Recovery Procedure
1. **Asset Restructure**: Sync versioned storage bucket from secondary replica.
2. **Hash Verification**: Scan all restored media objects against `source_documents.file_hash_sha256`.
3. **Quarantine Malicious Files**: Any missing or hash-mismatched files are flagged for re-ingestion from verified backup archives.

---

### 2.3 Redis Recovery Strategy (Recoverable vs. Rebuildable)

Redis operates strictly as a volatile cache, rate-limiting store, and ephemeral message broker. No authoritative application data is stored exclusively in Redis.

| Redis Subsystem | Recovery Classification | Action on Loss / Failure |
| :--- | :--- | :--- |
| **Rate Limit Counters** | **Rebuildable** | Evict state; counters reset naturally on next window. |
| **User JWT Blacklist** | **Recoverable** | Re-populated from database `revoked_tokens` table. |
| **Active Socratic Sessions** | **Rebuildable** | Re-loaded automatically from `tutor_sessions` DB records on next student turn. |
| **Celery Queue State** | **Rebuildable** | Unacknowledged background jobs are re-queued from database `notifications` / `audit_logs` pending state. |

---

### 2.4 AI System Traceability & Failover Strategy

#### Multi-Provider Automated Fallback
To ensure uninterrupted Socratic tutoring during LLM provider outages (e.g. OpenAI/Anthropic service degradation):
1. **Health Circuit Breaker**: `ModelRouter` monitors API status and latency.
2. **Automatic Failover**: If the primary provider throws a 5xx, rate limit, or timeout exception, `ModelRouter.execute_task` automatically routes request execution to the secondary fallback adapter (`mock` / alternative provider).
3. **Traceability Preservation**: The fallback execution logs a `ModelUsageRecord` with `validation_result="FALLBACK_USED"` and `failure_reason="Primary provider outage: <details>"`, maintaining 100% auditability for token usage, latency, and costs.

---

## 3. Incident Response Runbooks (5 Failure Scenarios)

### Scenario A: Total Database Outage or Data Corruption
1. **Trigger**: DB connection failure, corrupted tables, or inadvertent data modification.
2. **Action Steps**:
   1. Isolate primary database and declare DR incident.
   2. Execute automated restore:
      ```bash
      python -m backend.scripts.dr_backup_restore --action restore --archive dr_backup_latest.tar.gz
      ```
   3. Replay WAL logs to last valid timestamp ($RPO < 5\text{ mins}$).
   4. Run verification suite: `python -m pytest backend/tests/dr/test_restore_drill.py`.
   5. Re-route backend application traffic to restored database node ($RTO < 15\text{ mins}$).

### Scenario B: Object Storage Corruption or Bucket Deletion
1. **Trigger**: Missing curriculum PDFs or hash verification failures.
2. **Action Steps**:
   1. Enable bucket versioning rollback.
   2. Sync object storage backup folder via `dr_backup_restore.py`.
   3. Verify SHA-256 hashes against `source_documents` database records.

### Scenario C: Redis Cluster Crash or Cache Loss
1. **Trigger**: Redis process failure or memory corruption.
2. **Action Steps**:
   1. Restart Redis instance with empty cache.
   2. Re-populate JWT token blacklist from DB.
   3. Active user sessions auto-hydrate from `tutor_sessions` table on next user request.

### Scenario D: Celery Background Worker Failure
1. **Trigger**: Worker worker process death or stuck job queues.
2. **Action Steps**:
   1. Restart Celery worker pool: `celery -A backend.workers.celery_worker worker`.
   2. Process pending jobs from Dead Letter Queue (DLQ).
   3. Verify no grading or adaptive transactions were blocked (grading transactions are fully decoupled from notifications).

### Scenario E: Primary AI Provider Outage
1. **Trigger**: Primary AI API HTTP 503, timeout, or rate-limiting.
2. **Action Steps**:
   1. `ModelRouter` catches primary provider exception automatically.
   2. Request is automatically routed to fallback provider adapter.
   3. Fallback record is committed to `model_usage` table with `validation_result="FALLBACK_USED"`.
   4. Admin notified via observability logger.

---

## 4. Disaster Recovery Restore Drill Log

### Automated Restore Drill Verification
- **Drill Date**: August 14, 2026
- **Test Suite**: `backend/tests/dr/test_restore_drill.py`
- **Execution Result**: **SUCCESS (100% Pass Rate)**

```text
DR RESTORE DRILL VERIFICATION SUMMARY:
======================================================
1. Baseline Setup: Organizations, Users, Curricula, Attempts, Mastery, AI Logs -> CREATED
2. DR Backup Package Creation -> SUCCESS (SHA-256 verified)
3. Simulated Database & Asset Wipe -> COMPLETED (0 records remaining)
4. Database & Object Storage Restoration -> COMPLETED
5. Post-Restore Verification:
   - Organization Record Parity: 100% MATCH
   - User Account Record Parity: 100% MATCH
   - Curriculum & Concept Parity: 100% MATCH
   - Student Mastery EWMA Score Match: 100% MATCH (Score: 0.85, Band: Strong 🌟)
   - Object Storage File Hash Parity: 100% MATCH (SHA-256 verified)
   - AI Traceability Log Parity: 100% MATCH (Validation result & tokens intact)
   - AI Provider Outage Failover Test: 100% MATCH (Fallback executed, provenance preserved)
======================================================
STATUS: DISASTER RECOVERY RESTORATION TESTED AND VERIFIED.
```
