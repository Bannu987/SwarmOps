-- ============================================================
-- SWARMOPS PART C: SIGNALS, OPPORTUNITIES, SCAN HISTORY
-- Run this in Supabase Dashboard → SQL Editor
-- Run AFTER the base SUPABASE_SCHEMA.sql
-- ============================================================

-- 1. Signals (detected changes/issues/opportunities from scanners)
CREATE TABLE IF NOT EXISTS signals (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  project_id UUID REFERENCES projects(id) ON DELETE SET NULL,

  -- Classification
  signal_type TEXT NOT NULL CHECK (signal_type IN (
    'risk_alert', 'opportunity_window', 'competitor_move',
    'traffic_anomaly', 'ranking_change', 'content_decay'
  )),
  severity TEXT NOT NULL DEFAULT 'medium' CHECK (severity IN ('critical', 'high', 'medium', 'low')),
  category TEXT NOT NULL DEFAULT 'market' CHECK (category IN (
    'risk', 'opportunity', 'market', 'content', 'seo', 'analytics'
  )),

  -- Content
  title TEXT NOT NULL,
  description TEXT DEFAULT '',
  source_agent TEXT NOT NULL DEFAULT 'system',
  source_detail TEXT,  -- URL, file name, etc.

  -- Evidence trail (array of {claim, source, value})
  evidence JSONB DEFAULT '[]'::jsonb,
  raw_data JSONB DEFAULT '{}'::jsonb,

  -- Lifecycle
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'addressed', 'dismissed', 'expired')),
  seen BOOLEAN DEFAULT false,

  -- Timestamps
  detected_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Opportunities (RICE-scored actions from the opportunity engine)
CREATE TABLE IF NOT EXISTS opportunities (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  project_id UUID REFERENCES projects(id) ON DELETE SET NULL,

  -- Content
  title TEXT NOT NULL,
  description TEXT DEFAULT '',
  category TEXT NOT NULL DEFAULT 'seo' CHECK (category IN (
    'seo', 'content', 'cro', 'aeo', 'analytics', 'market'
  )),

  -- Source signals that triggered this opportunity
  signal_ids UUID[] DEFAULT ARRAY[]::UUID[],

  -- Recommendation details
  recommended_action TEXT NOT NULL,
  expected_impact TEXT NOT NULL DEFAULT 'medium' CHECK (expected_impact IN ('high', 'medium', 'low')),
  effort TEXT NOT NULL DEFAULT 'medium' CHECK (effort IN ('low', 'medium', 'high')),
  timeframe TEXT DEFAULT 'next 30 days',

  -- Scoring
  rice_score NUMERIC DEFAULT 0.0,
  confidence NUMERIC DEFAULT 0.5,

  -- Attribution
  proposed_by TEXT NOT NULL DEFAULT 'system',
  endorsed_by TEXT[] DEFAULT ARRAY[]::TEXT[],

  -- Lifecycle
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'in_progress', 'completed', 'dismissed')),
  user_action TEXT,  -- what the user said they did

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Scan history (tracks when each scanner last ran per user/project)
CREATE TABLE IF NOT EXISTS scan_history (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
  scanner_name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'success', 'no_change', 'failed')),
  signals_created INTEGER DEFAULT 0,
  duration_ms INTEGER,
  error_message TEXT,
  started_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users CRUD own signals" ON signals FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users CRUD own opportunities" ON opportunities FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users view own scan history" ON scan_history FOR SELECT USING (auth.uid() = user_id);

-- Allow service role (backend) to insert scan_history without auth
CREATE POLICY "Service role insert scan_history" ON scan_history FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role update scan_history" ON scan_history FOR UPDATE USING (true);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_signals_user_id ON signals(user_id);
CREATE INDEX IF NOT EXISTS idx_signals_user_status ON signals(user_id, status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_signals_project_id ON signals(project_id);
CREATE INDEX IF NOT EXISTS idx_signals_detected_at ON signals(user_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_severity ON signals(user_id, severity);

CREATE INDEX IF NOT EXISTS idx_opportunities_user_id ON opportunities(user_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_user_status ON opportunities(user_id, status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_opportunities_rice ON opportunities(user_id, rice_score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_project_id ON opportunities(project_id);

CREATE INDEX IF NOT EXISTS idx_scan_history_user_scanner ON scan_history(user_id, scanner_name, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_scan_history_project ON scan_history(project_id);

-- ============================================================
-- AUTO-UPDATE TIMESTAMPS
-- ============================================================

CREATE TRIGGER update_signals_updated_at BEFORE UPDATE ON signals
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_opportunities_updated_at BEFORE UPDATE ON opportunities
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- EXPIRE STALE SIGNALS (run via pg_cron or on-demand)
-- ============================================================

CREATE OR REPLACE FUNCTION expire_stale_signals()
RETURNS INTEGER AS $$
DECLARE
  expired_count INTEGER;
BEGIN
  UPDATE signals
  SET status = 'expired'
  WHERE status = 'active'
    AND expires_at IS NOT NULL
    AND expires_at < now();

  GET DIAGNOSTICS expired_count = ROW_COUNT;
  RETURN expired_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- DONE
-- To verify: SELECT COUNT(*) FROM signals; SELECT COUNT(*) FROM opportunities;
-- ============================================================
