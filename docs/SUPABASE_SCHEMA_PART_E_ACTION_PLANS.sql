-- ============================================================
-- SWARMOPS PART E: ACTION PLAN ENGINE
-- Run this in Supabase Dashboard → SQL Editor
-- ============================================================

CREATE TABLE IF NOT EXISTS action_plans (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
  
  -- Metadata
  source_type TEXT NOT NULL DEFAULT 'user' CHECK (source_type IN ('opportunity', 'swarm_decision', 'strategy_brief', 'user')),
  source_id UUID,
  
  title TEXT NOT NULL,
  objective TEXT NOT NULL,
  plan_type TEXT NOT NULL DEFAULT 'general_strategy' CHECK (plan_type IN (
    'seo_growth', 'paid_ads', 'lead_generation', 'content_calendar', 
    'crm_lifecycle', 'product_launch', 'competitor_attack', 
    'conversion_rate_optimization', 'general_strategy'
  )),
  
  priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('high', 'medium', 'low')),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked', 'dismissed')),
  owner_label TEXT DEFAULT 'nexus',
  due_date TIMESTAMPTZ,
  
  -- Effort and Impact Estimates
  estimated_effort TEXT DEFAULT 'medium' CHECK (estimated_effort IN ('low', 'medium', 'high')),
  expected_impact TEXT DEFAULT 'medium' CHECK (expected_impact IN ('low', 'medium', 'high')),
  confidence NUMERIC DEFAULT 0.5,
  
  -- Structured details
  tasks JSONB DEFAULT '[]'::JSONB,
  kpis JSONB DEFAULT '[]'::JSONB,
  dependencies JSONB DEFAULT '[]'::JSONB,
  risks JSONB DEFAULT '[]'::JSONB,
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE action_plans ENABLE ROW LEVEL SECURITY;

-- Scoped entirely by user_id
CREATE POLICY "Users CRUD own action plans" ON action_plans 
  FOR ALL USING (auth.uid() = user_id);

-- Allow service role (backend) to write action plans without auth token
CREATE POLICY "Service role insert action plans" ON action_plans FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role update action plans" ON action_plans FOR UPDATE USING (true);
CREATE POLICY "Service role delete action plans" ON action_plans FOR DELETE USING (true);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_plans_user_project ON action_plans(user_id, project_id);
CREATE INDEX IF NOT EXISTS idx_plans_project_status ON action_plans(project_id, status);
CREATE INDEX IF NOT EXISTS idx_plans_project_type ON action_plans(project_id, plan_type);
CREATE INDEX IF NOT EXISTS idx_plans_opp_id ON action_plans(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_plans_created_at ON action_plans(created_at DESC);

-- Auto-update timestamps
CREATE TRIGGER update_action_plans_updated_at BEFORE UPDATE ON action_plans
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
