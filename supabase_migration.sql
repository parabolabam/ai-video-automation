-- Supabase SQL to create conversation_state table
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS conversation_state (
    key TEXT PRIMARY KEY,
    response_id TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add an index for faster lookups
CREATE INDEX IF NOT EXISTS idx_conversation_state_key ON conversation_state(key);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE conversation_state ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow the service role to access all rows
CREATE POLICY "Allow service role access" ON conversation_state
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Optional: Add an update trigger to auto-update the timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_conversation_state_updated_at
    BEFORE UPDATE ON conversation_state
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
