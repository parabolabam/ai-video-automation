-- Platform Migration SQL
-- Run this in Supabase SQL Editor

-- 1. Profiles Table (if not already exists, standard Supabase pattern)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Auto-create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to call the function when a new user is created
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- 2. Workflows Table
CREATE TABLE IF NOT EXISTS workflows (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Agents Table
CREATE TABLE IF NOT EXISTS agents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL, -- e.g. "Researcher", "Analyst"
    model TEXT NOT NULL DEFAULT 'gpt-4o',
    system_instructions TEXT NOT NULL,
    tools TEXT[], -- Array of tool IDs e.g. ['web_search', 'fact_check']
    output_schema JSONB, -- Optional Pydantic schema definition
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Workflow Connections (The Graph)
CREATE TABLE IF NOT EXISTS workflow_connections (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE NOT NULL,
    from_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL, -- Null means start of flow
    to_agent_id UUID REFERENCES agents(id) ON DELETE CASCADE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Executions (Traceability)
CREATE TABLE IF NOT EXISTS executions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending', -- pending, running, completed, failed
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    input_params JSONB,
    error_message TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_workflows_user_id ON workflows(user_id);
CREATE INDEX IF NOT EXISTS idx_agents_workflow_id ON agents(workflow_id);
CREATE INDEX IF NOT EXISTS idx_connections_workflow_id ON workflow_connections(workflow_id);
CREATE INDEX IF NOT EXISTS idx_executions_workflow_id ON executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_executions_user_id ON executions(user_id);

-- RLS Policies (Simplified for Service Role access, but good practice to enable)
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE executions ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service role full access workflows" ON workflows FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access agents" ON agents FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access connections" ON workflow_connections FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access executions" ON executions FOR ALL USING (true) WITH CHECK (true);

-- Trigger for updated_at on workflows
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_workflows_updated_at
    BEFORE UPDATE ON workflows
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
