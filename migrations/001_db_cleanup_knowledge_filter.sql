-- ============================================================
-- Migration: DB Cleanup + Knowledge Filter System
-- Date: 2026-05-08
-- Purpose: Add columns for dedup/filter/vacuum, create job
--          tracking table, drop legacy historial_chat
-- ============================================================

-- 1. Add new columns to messages table
ALTER TABLE messages ADD COLUMN IF NOT EXISTS normalized_text TEXT;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS last_used_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS access_count INT DEFAULT 0;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS has_chinese BOOLEAN DEFAULT FALSE;

-- 2. Backfill has_chinese for existing rows
UPDATE messages SET has_chinese = (content ~ '[\u4e00-\u9fff]') WHERE has_chinese IS NULL OR has_chinese = FALSE;

-- 3. Backfill normalized_text for existing rows
UPDATE messages SET normalized_text = lower(regexp_replace(content, '[^\w\s]', '', 'g')) WHERE normalized_text IS NULL;

-- 4. Create indexes
CREATE INDEX IF NOT EXISTS idx_messages_normalized ON messages (normalized_text);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages (conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_access ON messages (access_count, created_at);

-- 5. Create vacuum_jobs table for async job tracking
CREATE TABLE IF NOT EXISTS vacuum_jobs (
    job_id UUID PRIMARY KEY,
    status TEXT DEFAULT 'pending',          -- pending, in_progress, completed, failed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    progress INT DEFAULT 0,                 -- 0-100 percentage
    current_stage TEXT,                     -- dedup, quality_filter, utility_decay, n_limit, db_optimization
    stats JSONB DEFAULT '{}',
    error_log TEXT
);

-- 6. Drop legacy table
DROP TABLE IF EXISTS historial_chat;

-- 7. Run VACUUM ANALYZE to update planner stats
VACUUM ANALYZE messages;
