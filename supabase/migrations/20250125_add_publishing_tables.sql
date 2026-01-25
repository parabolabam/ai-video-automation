-- ============================================================
-- CONNECTED ACCOUNTS (Multi-account support)
-- ============================================================
-- Supports multiple accounts per platform per user
-- e.g., User can have 3 YouTube channels connected

CREATE TABLE IF NOT EXISTS connected_accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  platform TEXT NOT NULL,  -- 'youtube', 'instagram', 'tiktok'

  -- Account identification
  platform_account_id TEXT NOT NULL,  -- YouTube channel ID, IG user ID
  account_name TEXT NOT NULL,          -- Display name (channel/account name)
  account_image_url TEXT,              -- Profile picture

  -- OAuth tokens (encrypted at rest by Supabase)
  access_token TEXT NOT NULL,
  refresh_token TEXT,
  token_expires_at TIMESTAMPTZ,

  -- Metadata
  connected_at TIMESTAMPTZ DEFAULT NOW(),
  last_used_at TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT true,

  -- Allow multiple accounts but not duplicates
  UNIQUE(user_id, platform, platform_account_id)
);

CREATE INDEX IF NOT EXISTS idx_connected_accounts_user ON connected_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_connected_accounts_platform ON connected_accounts(platform);

-- ============================================================
-- SCHEDULED POSTS (Scheduling queue)
-- ============================================================

CREATE TABLE IF NOT EXISTS scheduled_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Content
  video_url TEXT,              -- URL to video file (or local path reference)
  title TEXT NOT NULL,
  description TEXT,
  tags TEXT[],

  -- Targets (cross-posting support)
  target_account_ids UUID[] NOT NULL,  -- Array of connected_accounts.id

  -- Scheduling
  publish_at TIMESTAMPTZ NOT NULL,

  -- Status: pending, processing, completed, failed, cancelled
  status TEXT DEFAULT 'pending',
  error_message TEXT,

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scheduled_posts_user ON scheduled_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_status ON scheduled_posts(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_publish_at ON scheduled_posts(publish_at);

-- ============================================================
-- PUBLISH HISTORY (Track what was published where)
-- ============================================================

CREATE TABLE IF NOT EXISTS publish_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  scheduled_post_id UUID REFERENCES scheduled_posts(id) ON DELETE SET NULL,
  account_id UUID NOT NULL REFERENCES connected_accounts(id) ON DELETE CASCADE,

  -- Result
  platform TEXT NOT NULL,
  platform_post_id TEXT,       -- YouTube video ID, IG media ID
  platform_post_url TEXT,      -- Full URL to the published content

  -- Status
  status TEXT NOT NULL,        -- success, failed
  error_message TEXT,

  published_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_publish_history_user ON publish_history(user_id);
CREATE INDEX IF NOT EXISTS idx_publish_history_account ON publish_history(account_id);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE connected_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE publish_history ENABLE ROW LEVEL SECURITY;

-- Connected Accounts policies
DROP POLICY IF EXISTS "Users can view own accounts" ON connected_accounts;
CREATE POLICY "Users can view own accounts"
  ON connected_accounts FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own accounts" ON connected_accounts;
CREATE POLICY "Users can insert own accounts"
  ON connected_accounts FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own accounts" ON connected_accounts;
CREATE POLICY "Users can update own accounts"
  ON connected_accounts FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own accounts" ON connected_accounts;
CREATE POLICY "Users can delete own accounts"
  ON connected_accounts FOR DELETE USING (auth.uid() = user_id);

-- Scheduled Posts policies
DROP POLICY IF EXISTS "Users can view own posts" ON scheduled_posts;
CREATE POLICY "Users can view own posts"
  ON scheduled_posts FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own posts" ON scheduled_posts;
CREATE POLICY "Users can insert own posts"
  ON scheduled_posts FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own posts" ON scheduled_posts;
CREATE POLICY "Users can update own posts"
  ON scheduled_posts FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own posts" ON scheduled_posts;
CREATE POLICY "Users can delete own posts"
  ON scheduled_posts FOR DELETE USING (auth.uid() = user_id);

-- Publish History policies
DROP POLICY IF EXISTS "Users can view own history" ON publish_history;
CREATE POLICY "Users can view own history"
  ON publish_history FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own history" ON publish_history;
CREATE POLICY "Users can insert own history"
  ON publish_history FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================================
-- SERVICE ROLE POLICIES (for backend worker)
-- ============================================================
-- The service role key bypasses RLS, so no special policies needed
-- Backend uses SUPABASE_SERVICE_KEY for scheduled post processing
