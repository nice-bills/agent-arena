-- Supabase Schema for DeFi Agents Simulation
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABLE: runs
-- ============================================
CREATE TABLE IF NOT EXISTS runs (
    id SERIAL PRIMARY KEY,
    run_number INT NOT NULL UNIQUE,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'running',
    mechanics TEXT[] DEFAULT '{}',
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_runs_run_number ON runs(run_number);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);

-- ============================================
-- TABLE: agent_states
-- ============================================
CREATE TABLE IF NOT EXISTS agent_states (
    id SERIAL PRIMARY KEY,
    run_id INT REFERENCES runs(id) ON DELETE CASCADE,
    turn INT NOT NULL,
    agent_name TEXT NOT NULL,
    token_a_balance FLOAT DEFAULT 0,
    token_b_balance FLOAT DEFAULT 0,
    profit FLOAT DEFAULT 0,
    strategy TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for agent state queries
CREATE INDEX IF NOT EXISTS idx_agent_states_run_id ON agent_states(run_id);
CREATE INDEX IF NOT EXISTS idx_agent_states_turn ON agent_states(run_id, turn);
CREATE INDEX IF NOT EXISTS idx_agent_states_agent ON agent_states(agent_name);

-- ============================================
-- TABLE: pool_states
-- ============================================
CREATE TABLE IF NOT EXISTS pool_states (
    id SERIAL PRIMARY KEY,
    run_id INT REFERENCES runs(id) ON DELETE CASCADE,
    turn INT NOT NULL,
    reserve_a FLOAT DEFAULT 0,
    reserve_b FLOAT DEFAULT 0,
    price_ab FLOAT DEFAULT 0,
    total_liquidity FLOAT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for pool state queries
CREATE INDEX IF NOT EXISTS idx_pool_states_run_id ON pool_states(run_id);
CREATE INDEX IF NOT EXISTS idx_pool_states_turn ON pool_states(run_id, turn);

-- ============================================
-- TABLE: actions
-- ============================================
CREATE TABLE IF NOT EXISTS actions (
    id SERIAL PRIMARY KEY,
    run_id INT REFERENCES runs(id) ON DELETE CASCADE,
    turn INT NOT NULL,
    agent_name TEXT NOT NULL,
    action_type TEXT NOT NULL,
    payload JSONB DEFAULT '{}',
    reasoning_trace TEXT,
    thinking_trace TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for action queries
CREATE INDEX IF NOT EXISTS idx_actions_run_id ON actions(run_id);
CREATE INDEX IF NOT EXISTS idx_actions_turn ON actions(run_id, turn);
CREATE INDEX IF NOT EXISTS idx_actions_agent ON actions(agent_name);
CREATE INDEX IF NOT EXISTS idx_actions_type ON actions(action_type);

-- ============================================
-- TABLE: run_metrics
-- ============================================
CREATE TABLE IF NOT EXISTS run_metrics (
    id SERIAL PRIMARY KEY,
    run_id INT REFERENCES runs(id) ON DELETE CASCADE,
    gini_coefficient FLOAT,
    cooperation_rate FLOAT,
    betrayal_count INT DEFAULT 0,
    avg_agent_profit FLOAT,
    pool_stability FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for metrics queries
CREATE INDEX IF NOT EXISTS idx_run_metrics_run_id ON run_metrics(run_id);

-- ============================================
-- TABLE: agent_learning (optional - for persistence)
-- ============================================
CREATE TABLE IF NOT EXISTS agent_learning (
    id SERIAL PRIMARY KEY,
    agent_name TEXT NOT NULL,
    run_number INT NOT NULL,
    learning_summary TEXT,
    strategy_tendency TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for agent learning queries
CREATE INDEX IF NOT EXISTS idx_agent_learning_agent ON agent_learning(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_learning_run ON agent_learning(run_number);

-- ============================================
-- FUNCTIONS (optional utilities)
-- ============================================

-- Function to get the latest run number
CREATE OR REPLACE FUNCTION get_next_run_number()
RETURNS INT AS $$
BEGIN
    RETURN COALESCE((SELECT MAX(run_number) FROM runs), 0) + 1;
END;
$$ LANGUAGE plpgsql;

-- Function to update run end time
CREATE OR REPLACE FUNCTION complete_run(p_run_id INT)
RETURNS VOID AS $$
BEGIN
    UPDATE runs
    SET end_time = NOW(), status = 'completed'
    WHERE id = p_run_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- SAMPLE DATA (for testing)
-- ============================================

-- Insert a sample run
INSERT INTO runs (run_number, status, config)
VALUES (1, 'completed', '{"num_agents": 5, "turns_per_run": 10}'::jsonb)
ON CONFLICT (run_number) DO NOTHING;

-- ============================================
-- VERIFICATION QUERY
-- ============================================

-- Check all tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('runs', 'agent_states', 'pool_states', 'actions', 'run_metrics', 'agent_learning')
ORDER BY table_name;
