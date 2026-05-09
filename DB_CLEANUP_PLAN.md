# DB Cleanup + Knowledge Filter System

## 1. Overview

**Problem:** The `messages` table accumulates embeddings for every single chat message, including greetings, single-word responses, and conversational fluff. This bloats the pgvector index, slows down RAG similarity searches, and degrades Tars response latency.

**Goals:**
- Faster RAG retrieval by reducing vector pool size
- Smarter embedding strategy (embed only semantically useful messages)
- Non-blocking maintenance pipeline for long-running cleanup tasks
- Automatic deduplication to prevent redundant embeddings

**Scope:** `messages` table only. `historial_chat` table dropped (legacy, unused).

---

## 2. Architecture

### Layer 1: Synchronous Gateway (Real-Time)

When `save_long_term_memory()` is called:

```
Message arrives
    ↓
Normalize text (lowercase + strip punctuation)
    ↓
Sync dedup: SELECT id FROM messages WHERE normalized_text = ?
    ↓ (exists)
    → UPDATE last_used_timestamp → RETURN (skip embedding)
    ↓ (not found)
Knowledge filter: should_embed(text)?
    ↓ (no)
    → RETURN (skip embedding)
    ↓ (yes)
Generate embedding → INSERT with metadata → RETURN
```

### Layer 2: Async Vacuum Pipeline (Background/Cron)

Triggered via `POST /admin/vacuum` → returns `202 Accepted` with `job_id`.

Background worker executes 4 stages:

| Stage | Name | Action |
|-------|------|--------|
| A | Cosine Dedup | Find vectors with cosine similarity > 0.95, keep highest `access_count`, delete rest |
| B | Quality Filter | Delete where `(len < 10 AND no_chinese) OR is_common_greeting` |
| C | Utility Decay | Delete where `access_count = 0 AND age > 30 days` |
| D | N-Limit | Keep only last 500 messages per conversation, delete oldest |
| E | DB Optimization | `VACUUM ANALYZE messages` + `REINDEX` on vector index |

Job state machine: `pending` → `in_progress` → `completed` / `failed`

Poll via `GET /admin/vacuum/status/{job_id}` for progress percentage and stats.

---

## 3. Schema Changes

### New columns on `messages` table

```sql
ALTER TABLE messages ADD COLUMN IF NOT EXISTS normalized_text TEXT;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS last_used_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS access_count INT DEFAULT 0;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS has_chinese BOOLEAN DEFAULT FALSE;
```

### New indexes

```sql
CREATE INDEX IF NOT EXISTS idx_messages_normalized ON messages (normalized_text);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages (conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_access ON messages (access_count, created_at);
```

### New table: `vacuum_jobs`

```sql
CREATE TABLE IF NOT EXISTS vacuum_jobs (
    job_id UUID PRIMARY KEY,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    progress INT DEFAULT 0,
    current_stage TEXT,
    stats JSONB DEFAULT '{}',
    error_log TEXT
);
```

### Dropped

```sql
DROP TABLE IF EXISTS historial_chat;
```

---

## 4. Knowledge Filter

### Common Greetings Set (EN / ES / ZH)

```python
COMMON_GREETINGS = {
    # English
    "hi", "hello", "hey", "ok", "okay", "yes", "no", "thanks", "thank you",
    "bye", "goodbye", "see you", "sure", "cool", "nice", "good", "fine",
    # Spanish
    "hola", "adiós", "chao", "sí", "no", "gracias", "vale", "ok", "bien",
    "bueno", "claro", "perfecto",
    # Chinese
    "你好", "你好吗", "再见", "谢谢", "谢谢你", "好的", "是", "不是",
    "对", "不对", "嗯",
}
```

### Decision Rule

```
should_embed(text):
    normalized = normalize_text(text)
    if normalized in COMMON_GREETINGS → False
    if contains_chinese(text) → True  (Chinese exception)
    if len(text) < 10 → False
    → True
```

---

## 5. Deduplication Strategy

| Layer | Method | Threshold | Action |
|-------|--------|-----------|--------|
| Sync | Exact match on `normalized_text` | 100% | Update `last_used_timestamp`, skip embedding |
| Async | Cosine similarity on embeddings | > 0.95 | Keep row with highest `access_count`, delete rest |

---

## 6. API Endpoints

### POST /admin/vacuum

**Request:** None (MVP: open, no auth)

**Response (202 Accepted):**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending"
}
```

### GET /admin/vacuum/status/{job_id}

**Response:**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "in_progress",
    "progress": 60,
    "current_stage": "utility_decay",
    "stats": {
        "stage_a_dedup_deleted": 42,
        "stage_b_quality_deleted": 128
    },
    "created_at": "2026-05-08T03:00:00Z",
    "updated_at": "2026-05-08T03:00:15Z",
    "error_log": null
}
```

---

## 7. Cron Setup

**Script:** `scripts/run_vacuum.py`

```bash
# Run daily at 3:00 AM
0 3 * * * cd /home/lancelot/Personal_Projects/Tars && conda run -n agentes_ia python scripts/run_vacuum.py >> /var/log/tars_vacuum.log 2>&1
```

Or manual:
```bash
python scripts/run_vacuum.py
```

---

## 8. Files Changed

### New files
- `agents/RAG/filter.py` — knowledge filter functions
- `agents/RAG/vacuum.py` — async vacuum pipeline
- `scripts/run_vacuum.py` — cron/standalone runner

### Modified files
- `agents/RAG/save_memory.py` — add sync dedup + filter gate
- `agents/RAG/utils.py` — increment `access_count` on retrieval
- `api.py` — add `/admin/vacuum` and `/admin/vacuum/status` endpoints
- `setup_db.sql` — add migration SQL

### Deleted
- `historial_chat` table (via migration)

---

## 9. Testing Plan

1. **Unit tests:** `should_embed()` with greetings, Chinese text, short English, long English
2. **Integration:** Insert mock messages, run vacuum stages, verify correct deletions
3. **Manual:** Check `messages` table size before/after, verify RAG retrieval still works, measure latency improvement

---

## 10. Rollback Plan

1. **Revert migration:** Run reverse SQL (drop columns, drop indexes, drop `vacuum_jobs`)
2. **Restore `historial_chat`:** From backup if needed
3. **Kill switch:** Remove cron entry, skip filter in `save_memory.py` by setting env var `DISABLE_KNOWLEDGE_FILTER=1`
