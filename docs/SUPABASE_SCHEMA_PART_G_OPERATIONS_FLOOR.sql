-- ============================================================
-- SWARMOPS PART G: OPERATIONS FLOOR CONNECTION
-- Run this in Supabase Dashboard → SQL Editor
-- ============================================================

-- 1. Add new columns to action_plans table
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS signal_id UUID;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS signal_key TEXT;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS priority_score NUMERIC;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS recommended_fix TEXT;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS evidence JSONB DEFAULT NULL;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS implementation_steps TEXT;
ALTER TABLE action_plans ADD COLUMN IF NOT EXISTS verification_steps TEXT;

-- 2. Update status constraint to include new statuses
ALTER TABLE action_plans DROP CONSTRAINT IF EXISTS action_plans_status_check;
ALTER TABLE action_plans ADD CONSTRAINT action_plans_status_check CHECK (
  status IN ('pending', 'approved', 'in_progress', 'verified', 'rejected', 'completed', 'blocked', 'dismissed')
);
