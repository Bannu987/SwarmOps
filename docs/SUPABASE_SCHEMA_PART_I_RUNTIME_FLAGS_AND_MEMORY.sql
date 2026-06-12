-- SUPABASE_SCHEMA_PART_I_RUNTIME_FLAGS_AND_MEMORY.sql
-- Migration to add feature flags and structured project memory tables

-- Enable UUID extension if not already done
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: feature_flags
CREATE TABLE IF NOT EXISTS feature_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key TEXT NOT NULL,
    description TEXT,
    default_value BOOLEAN NOT NULL DEFAULT FALSE,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    scope_type TEXT NOT NULL DEFAULT 'global', -- 'global', 'project', 'workspace', 'user'
    scope_id UUID,
    rollout_percentage INT DEFAULT 100,
    conditions_json JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT unique_flag_scope UNIQUE (key, scope_type, scope_id)
);

-- Table: feature_flag_audit_log
CREATE TABLE IF NOT EXISTS feature_flag_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flag_key TEXT NOT NULL,
    old_value JSONB,
    new_value JSONB,
    scope_type TEXT NOT NULL,
    scope_id UUID,
    changed_by UUID,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Table: project_memory
CREATE TABLE IF NOT EXISTS project_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    project_id UUID NOT NULL,
    memory_type TEXT NOT NULL, -- brand_profile, website_summary, etc.
    title TEXT NOT NULL,
    summary TEXT,
    content JSONB DEFAULT '{}'::jsonb,
    source_type TEXT, -- boardroom_decision, action_plan, verification_history, etc.
    source_id TEXT,
    trace_id TEXT,
    confidence NUMERIC DEFAULT 0.8,
    trust_level TEXT DEFAULT 'system', -- 'system', 'user'
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Index for fast project-scoped lookup
CREATE INDEX IF NOT EXISTS idx_project_memory_lookup ON project_memory (project_id, user_id, memory_type);

-- Table: retrieval_logs
CREATE TABLE IF NOT EXISTS retrieval_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    project_id UUID,
    trace_id TEXT,
    query TEXT,
    retrieved_memory_ids JSONB DEFAULT '[]'::jsonb,
    memory_types JSONB DEFAULT '[]'::jsonb,
    retrieval_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Trigger to auto-update updated_at for feature_flags
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_feature_flags_modtime
    BEFORE UPDATE ON feature_flags
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- Trigger to auto-update updated_at for project_memory
CREATE TRIGGER update_project_memory_modtime
    BEFORE UPDATE ON project_memory
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();
