-- 002_production_schema.sql
-- Final production schema for AIMS Chatbot

-- Create leads table
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
CREATE INDEX IF NOT EXISTS idx_leads_session_id ON leads(session_id);

-- Create chat_logs table
CREATE TABLE IF NOT EXISTS chat_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query TEXT,
  response TEXT,
  session_id TEXT,
  user_email TEXT,
  confidence_score FLOAT,
  processing_time_ms INT,
  is_fallback BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_chat_logs_session ON chat_logs(session_id);
