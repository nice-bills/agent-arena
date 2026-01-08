-- Migration: Add run_summaries table
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS run_summaries (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    summary_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_run_summaries_run_id ON run_summaries(run_id);

-- Enable RLS (Row Level Security)
ALTER TABLE run_summaries ENABLE ROW LEVEL SECURITY;

-- Policy to allow read access
CREATE POLICY IF NOT EXISTS "Allow public read access" ON run_summaries
    FOR SELECT USING (true);

-- Policy to allow insert access (for authenticated users)
CREATE POLICY IF NOT EXISTS "Allow authenticated insert" ON run_summaries
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');
