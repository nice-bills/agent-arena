-- Wipe all test data and reset for public launch
-- Run this in Supabase SQL Editor

-- 1. Delete all data (order matters due to foreign keys)
DELETE FROM run_metrics;
DELETE FROM actions;
DELETE FROM pool_states;
DELETE FROM agent_states;
DELETE FROM agent_learning;
DELETE FROM runs;

-- 2. Reset sequence (PostgreSQL)
ALTER SEQUENCE runs_id_seq RESTART WITH 1;

-- 3. Verify
SELECT COUNT(*) as remaining_runs FROM runs;

-- 4. Insert a placeholder run to start fresh
INSERT INTO runs (run_number, status, config)
VALUES (0, 'completed', '{"initialized": true}'::jsonb)
ON CONFLICT DO NOTHING;

-- 5. Get next run number (should be 1)
SELECT get_next_run_number() as next_run;
