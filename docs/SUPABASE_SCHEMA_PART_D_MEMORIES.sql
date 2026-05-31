-- ============================================================
-- SWARMOPS PART D: PERSISTENT MARKETING MEMORY
-- Run this in Supabase Dashboard → SQL Editor
-- Run AFTER the signals/opportunities schema
-- ============================================================

CREATE TABLE IF NOT EXISTS project_memories (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  
  -- Memory classification
  memory_type TEXT NOT NULL CHECK (memory_type IN (
    'brand_voice', 'icp', 'competitor', 'campaign_goal', 'channel_strategy',
    'previous_decision', 'approved_action', 'rejected_action', 'data_gap',
    'experiment', 'report_insight'
  )),
  
  -- Memory content
  title TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  source TEXT NOT NULL DEFAULT 'user' CHECK (source IN ('user', 'swarm_decision', 'file_upload', 'scanner')),
  confidence NUMERIC DEFAULT 0.5,
  tags TEXT[] DEFAULT ARRAY[]::TEXT[],
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE project_memories ENABLE ROW LEVEL SECURITY;

-- Scoped entirely by user_id
CREATE POLICY "Users CRUD own project memories" ON project_memories 
  FOR ALL USING (auth.uid() = user_id);

-- Allow service role (backend) to write project memories without auth token
CREATE POLICY "Service role insert project memories" ON project_memories FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role update project memories" ON project_memories FOR UPDATE USING (true);
CREATE POLICY "Service role delete project memories" ON project_memories FOR DELETE USING (true);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_memories_user_project ON project_memories(user_id, project_id);
CREATE INDEX IF NOT EXISTS idx_memories_project_type ON project_memories(project_id, memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON project_memories(created_at DESC);

-- Auto-update timestamps
CREATE TRIGGER update_memories_updated_at BEFORE UPDATE ON project_memories
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
