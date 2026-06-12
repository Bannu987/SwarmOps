-- ============================================================
-- SWARMOPS PART H: END-TO-END OBSERVEABILITY & RELIABILITY SPINE
-- Run this in Supabase Dashboard → SQL Editor
-- ============================================================

-- 1. Create run_traces table
CREATE TABLE IF NOT EXISTS run_traces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id UUID NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    run_type VARCHAR(50) NOT NULL, -- 'website_scan' | 'signal_analysis'
    workflow_version VARCHAR(20) NOT NULL,
    prompt_version VARCHAR(20) NOT NULL,
    model_name VARCHAR(100),
    provider VARCHAR(50),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'running', -- 'running' | 'completed' | 'failed'
    latency_ms INTEGER,
    tokens_in INTEGER,
    tokens_out INTEGER,
    error_type VARCHAR(100),
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_run_traces_trace_id ON run_traces(trace_id);
CREATE INDEX IF NOT EXISTS idx_run_traces_project_id ON run_traces(project_id);

-- 2. Create agent_step_logs table
CREATE TABLE IF NOT EXISTS agent_step_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id UUID NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    input_snapshot JSONB DEFAULT '{}'::jsonb,
    output_snapshot JSONB DEFAULT '{}'::jsonb,
    schema_valid BOOLEAN DEFAULT TRUE,
    tool_used VARCHAR(100),
    fallback_used BOOLEAN DEFAULT FALSE,
    error_type VARCHAR(100),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    ended_at TIMESTAMP WITH TIME ZONE,
    latency_ms INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_agent_step_logs_trace_id ON agent_step_logs(trace_id);

-- 3. Create stream_events table
CREATE TABLE IF NOT EXISTS stream_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id UUID NOT NULL,
    channel VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    sequence_no INTEGER NOT NULL,
    payload_size INTEGER,
    connection_status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_stream_events_trace_id ON stream_events(trace_id);

-- 4. Update action_plans table to support trace_id and observability metadata
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS trace_id UUID;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS observability_metadata JSONB DEFAULT '{}'::jsonb;

-- 5. Enable RLS
ALTER TABLE run_traces ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_step_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE stream_events ENABLE ROW LEVEL SECURITY;

-- 6. RLS Policies
CREATE POLICY "Allow users to read their own run traces" ON run_traces
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Allow admin role to manage run traces" ON run_traces
    FOR ALL USING (true);

CREATE POLICY "Allow users to read their own agent step logs" ON agent_step_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM run_traces rt 
            WHERE rt.trace_id = agent_step_logs.trace_id AND rt.user_id = auth.uid()
        )
    );

CREATE POLICY "Allow admin role to manage agent step logs" ON agent_step_logs
    FOR ALL USING (true);

CREATE POLICY "Allow users to read their own stream events" ON stream_events
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM run_traces rt 
            WHERE rt.trace_id = stream_events.trace_id AND rt.user_id = auth.uid()
        )
    );

CREATE POLICY "Allow admin role to manage stream events" ON stream_events
    FOR ALL USING (true);
