-- ============================================================
-- SWARMOPS PART F: SIGNAL INTELLIGENCE ENGINE V1
-- Optimized for Supabase Dashboard → SQL Editor Execution
-- ============================================================

-- 1. Alter existing signals table to add fingerprinting & tracking
ALTER TABLE signals ADD COLUMN IF NOT EXISTS fingerprint TEXT;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS occurrence_count INTEGER DEFAULT 1;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE signals ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_signals_fingerprint ON signals(fingerprint);

-- 2. Scan runs table
CREATE TABLE IF NOT EXISTS scan_runs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'success', 'failed')),
  total_pages_scanned INTEGER DEFAULT 0,
  total_signals_detected INTEGER DEFAULT 0,
  started_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ,
  error_message TEXT
);

-- 3. Scan pages table (individual page audit telemetry)
CREATE TABLE IF NOT EXISTS scan_pages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  scan_run_id UUID REFERENCES scan_runs(id) ON DELETE CASCADE NOT NULL,
  url TEXT NOT NULL,
  status_code INTEGER,
  response_time_ms INTEGER,
  page_title TEXT,
  meta_description TEXT,
  h1_content TEXT,
  crawled_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Signal occurrences (page-level instances of a signal)
CREATE TABLE IF NOT EXISTS signal_occurrences (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  signal_id UUID REFERENCES signals(id) ON DELETE CASCADE NOT NULL,
  scan_run_id UUID REFERENCES scan_runs(id) ON DELETE SET NULL,
  page_url TEXT NOT NULL,
  detected_at TIMESTAMPTZ DEFAULT now()
);

-- 5. Signal evidence (granular evidence details)
CREATE TABLE IF NOT EXISTS signal_evidence (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  signal_id UUID REFERENCES signals(id) ON DELETE CASCADE NOT NULL,
  scan_run_id UUID REFERENCES scan_runs(id) ON DELETE SET NULL,
  url TEXT NOT NULL,
  detector_source TEXT NOT NULL,
  http_status INTEGER,
  dom_evidence TEXT,
  extracted_tag TEXT,
  condition TEXT,
  confidence NUMERIC DEFAULT 1.0,
  source_type TEXT CHECK (source_type IN ('crawler', 'html', 'api', 'heuristic', 'user')),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 6. Agent runs (audit trail of LLM specialist and supervisor executions)
CREATE TABLE IF NOT EXISTS agent_runs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  signal_id UUID REFERENCES signals(id) ON DELETE SET NULL,
  agent_id TEXT NOT NULL,
  workflow_name TEXT,
  inputs JSONB DEFAULT '{}'::jsonb,
  outputs JSONB DEFAULT '{}'::jsonb,
  status TEXT DEFAULT 'started' CHECK (status IN ('started', 'completed', 'failed')),
  latency_ms INTEGER,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 7. Action items (granular items for action plans)
CREATE TABLE IF NOT EXISTS action_items (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  plan_id UUID REFERENCES action_plans(id) ON DELETE CASCADE NOT NULL,
  title TEXT NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'blocked')),
  assigned_to TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);

-- 8. Approvals (for Swarm proposed actions)
CREATE TABLE IF NOT EXISTS approvals (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  signal_id UUID REFERENCES signals(id) ON DELETE SET NULL,
  plan_id UUID REFERENCES action_plans(id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
  created_at TIMESTAMPTZ DEFAULT now(),
  decided_at TIMESTAMPTZ
);

-- 9. Rescans (on-demand verification trigger)
CREATE TABLE IF NOT EXISTS rescans (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  signal_id UUID REFERENCES signals(id) ON DELETE CASCADE NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
  triggered_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);

-- 10. Project snapshots
CREATE TABLE IF NOT EXISTS project_snapshots (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  seo_score NUMERIC,
  aeo_score NUMERIC,
  tracking_score NUMERIC,
  conversion_score NUMERIC,
  trust_score NUMERIC,
  overall_score NUMERIC,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 11. Health scores
CREATE TABLE IF NOT EXISTS health_scores (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL UNIQUE,
  overall_score NUMERIC DEFAULT 100.0,
  seo_score NUMERIC DEFAULT 100.0,
  aeo_score NUMERIC DEFAULT 100.0,
  tracking_score NUMERIC DEFAULT 100.0,
  conversion_score NUMERIC DEFAULT 100.0,
  trust_score NUMERIC DEFAULT 100.0,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 12. Health score factors
CREATE TABLE IF NOT EXISTS health_score_factors (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  health_score_id UUID REFERENCES health_scores(id) ON DELETE CASCADE NOT NULL,
  signal_type TEXT NOT NULL,
  impact_deduction NUMERIC NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- ROW LEVEL SECURITY (RLS) & SCOPED POLICIES
-- ============================================================

ALTER TABLE scan_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE signal_occurrences ENABLE ROW LEVEL SECURITY;
ALTER TABLE signal_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE action_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE rescans ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_score_factors ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users CRUD own scan_runs" ON scan_runs FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users CRUD own scan_pages" ON scan_pages FOR ALL USING (
  scan_run_id IN (SELECT id FROM scan_runs WHERE user_id = auth.uid())
);
CREATE POLICY "Users CRUD own signal_occurrences" ON signal_occurrences FOR ALL USING (
  signal_id IN (SELECT id FROM signals WHERE user_id = auth.uid())
);
CREATE POLICY "Users CRUD own signal_evidence" ON signal_evidence FOR ALL USING (
  signal_id IN (SELECT id FROM signals WHERE user_id = auth.uid())
);
CREATE POLICY "Users CRUD own agent_runs" ON agent_runs FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users CRUD own action_items" ON action_items FOR ALL USING (
  plan_id IN (SELECT id FROM action_plans WHERE user_id = auth.uid())
);
CREATE POLICY "Users CRUD own approvals" ON approvals FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users CRUD own rescans" ON rescans FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users CRUD own project_snapshots" ON project_snapshots FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users CRUD own health_scores" ON health_scores FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users CRUD own health_score_factors" ON health_score_factors FOR ALL USING (
  health_score_id IN (SELECT id FROM health_scores WHERE user_id = auth.uid())
);

-- ============================================================
-- PERFORMANCE INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_scan_runs_project ON scan_runs(project_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_scan_pages_run ON scan_pages(scan_run_id);
CREATE INDEX IF NOT EXISTS idx_signal_occurrences_sig ON signal_occurrences(signal_id);
CREATE INDEX IF NOT EXISTS idx_signal_evidence_sig ON signal_evidence(signal_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_sig ON agent_runs(signal_id);
CREATE INDEX IF NOT EXISTS idx_action_items_plan ON action_items(plan_id);
CREATE INDEX IF NOT EXISTS idx_approvals_user_status ON approvals(user_id, status);
CREATE INDEX IF NOT EXISTS idx_rescans_sig ON rescans(signal_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_project ON project_snapshots(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_factors_score ON health_score_factors(health_score_id);

-- ============================================================
-- DYNAMIC TELEMETRY TRIGGERS
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_health_scores_updated_at ON health_scores;
CREATE TRIGGER update_health_scores_updated_at BEFORE UPDATE ON health_scores
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
