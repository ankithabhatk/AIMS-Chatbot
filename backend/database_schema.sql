-- AIMS Chatbot Database Schema
-- Run this in Supabase SQL Editor

-- Create leads table for session persistence
CREATE TABLE IF NOT EXISTS leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT UNIQUE,
  name TEXT,
  email TEXT,
  phone TEXT,
  interest TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Enable Row Level Security (optional - for user-specific data)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Create policy for service role (full access)
CREATE POLICY "Enable service_role access" ON leads
  FOR ALL USING (true) WITH CHECK (true);

-- Create index for faster session lookups
CREATE INDEX IF NOT EXISTS idx_leads_session_id ON leads(session_id);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);

-- UPSERT function for idempotent inserts
-- Prevents duplicates when same session_id is used
CREATE OR REPLACE FUNCTION upsert_lead(
  p_session_id TEXT,
  p_name TEXT,
  p_email TEXT,
  p_phone TEXT DEFAULT NULL,
  p_interest TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
  v_id UUID;
BEGIN
  INSERT INTO leads (session_id, name, email, phone, interest, updated_at)
  VALUES (p_session_id, p_name, p_email, p_phone, p_interest, NOW())
  ON CONFLICT (session_id) DO UPDATE SET
    name = COALESCE(EXCLUDED.name, leads.name),
    email = COALESCE(EXCLUDED.email, leads.email),
    phone = COALESCE(EXCLUDED.phone, leads.phone),
    interest = COALESCE(EXCLUDED.interest, leads.interest),
    updated_at = NOW()
  RETURNING id INTO v_id;
  
  RETURN v_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;