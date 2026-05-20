-- ============================================================
-- SWARMOPS V2 DATABASE SCHEMA
-- Run this in Supabase Dashboard → SQL Editor
-- ============================================================

-- 1. User profiles (extends auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email TEXT,
  full_name TEXT,
  avatar_url TEXT,
  company TEXT,
  industry TEXT,
  website_url TEXT,
  language TEXT DEFAULT 'en',
  theme TEXT DEFAULT 'dark',
  onboarding_complete BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Projects (workspaces)
CREATE TABLE IF NOT EXISTS projects (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  website_url TEXT,
  brand_data JSONB DEFAULT '{}'::jsonb,
  pinned BOOLEAN DEFAULT false,
  archived BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Conversations
CREATE TABLE IF NOT EXISTS conversations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
  title TEXT DEFAULT 'New Conversation',
  pinned BOOLEAN DEFAULT false,
  archived BOOLEAN DEFAULT false,
  message_count INTEGER DEFAULT 0,
  last_message_at TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Messages
CREATE TABLE IF NOT EXISTS messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE NOT NULL,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  agents_used TEXT[] DEFAULT ARRAY[]::TEXT[],
  workflow TEXT,
  latency_ms INTEGER,
  confidence NUMERIC,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 5. User credentials (per-user API keys)
CREATE TABLE IF NOT EXISTS user_credentials (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  service TEXT NOT NULL,
  credentials JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT DEFAULT 'active',
  last_used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, service)
);

-- 6. Artifacts (blog posts, campaigns, schemas)
CREATE TABLE IF NOT EXISTS artifacts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
  project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
  artifact_type TEXT NOT NULL,
  title TEXT,
  content JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'deployed')),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 7. File uploads
CREATE TABLE IF NOT EXISTS file_uploads (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
  filename TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_size INTEGER,
  storage_path TEXT NOT NULL,
  extracted_text TEXT,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_uploads ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users insert own profile" ON profiles FOR INSERT WITH CHECK (auth.uid() = id);

-- Projects policies
CREATE POLICY "Users CRUD own projects" ON projects FOR ALL USING (auth.uid() = user_id);

-- Conversations policies
CREATE POLICY "Users CRUD own conversations" ON conversations FOR ALL USING (auth.uid() = user_id);

-- Messages policies
CREATE POLICY "Users CRUD own messages" ON messages FOR ALL USING (auth.uid() = user_id);

-- Credentials policies
CREATE POLICY "Users CRUD own credentials" ON user_credentials FOR ALL USING (auth.uid() = user_id);

-- Artifacts policies
CREATE POLICY "Users CRUD own artifacts" ON artifacts FOR ALL USING (auth.uid() = user_id);

-- File uploads policies
CREATE POLICY "Users CRUD own files" ON file_uploads FOR ALL USING (auth.uid() = user_id);

-- ============================================================
-- INDEXES (critical for RLS performance)
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_pinned ON projects(user_id, pinned) WHERE pinned = true;
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_project_id ON conversations(project_id);
CREATE INDEX IF NOT EXISTS idx_conversations_last_message ON conversations(user_id, last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_credentials_user_id ON user_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_user_id ON artifacts(user_id, status);
CREATE INDEX IF NOT EXISTS idx_files_user_id ON file_uploads(user_id);

-- ============================================================
-- AUTO-CREATE PROFILE ON SIGNUP
-- ============================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1))
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- UPDATE TIMESTAMPS
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_artifacts_updated_at BEFORE UPDATE ON artifacts
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- DONE
-- ============================================================
