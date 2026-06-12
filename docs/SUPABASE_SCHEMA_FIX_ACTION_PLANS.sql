-- ============================================================
-- SWARMOPS: FIX ACTION PLANS TABLE SCHEMA
-- Run this in Supabase Dashboard -> SQL Editor
-- This ensures all Phase 2 columns exist on older tables.
-- ============================================================

-- Add all Phase 2 Base Columns (from PART E)
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS source_type TEXT DEFAULT 'user';
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS source_id UUID;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS objective TEXT;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS plan_type TEXT DEFAULT 'general_strategy';
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS priority TEXT DEFAULT 'medium';
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS owner_label TEXT DEFAULT 'nexus';
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS due_date TIMESTAMPTZ;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS estimated_effort TEXT DEFAULT 'medium';
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS expected_impact TEXT DEFAULT 'medium';
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS confidence NUMERIC DEFAULT 0.5;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS tasks JSONB DEFAULT '[]'::JSONB;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS kpis JSONB DEFAULT '[]'::JSONB;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS dependencies JSONB DEFAULT '[]'::JSONB;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS risks JSONB DEFAULT '[]'::JSONB;

-- Add all Phase 2.5 Boardroom Output Columns (from PART G)
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS signal_id UUID;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS signal_key TEXT;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS priority_score NUMERIC;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS recommended_fix TEXT;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS evidence JSONB DEFAULT NULL;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS implementation_steps TEXT;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS verification_steps TEXT;

-- Drop constraints safely if needed and re-apply
ALTER TABLE action_plans DROP CONSTRAINT IF EXISTS action_plans_status_check;
ALTER TABLE action_plans ADD CONSTRAINT action_plans_status_check CHECK (
  status IN ('pending', 'approved', 'in_progress', 'verified', 'rejected', 'completed', 'blocked', 'dismissed')
);

-- Note: In postgrest, after altering schema, you MUST reload the schema cache so the API recognizes new columns!
NOTIFY pgrst, 'reload schema';
