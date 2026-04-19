-- AIMS College Chatbot - Database Schema
-- Supabase PostgreSQL Tables
-- Created: 2026-04-19

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Documents Table
-- Stores scraped website content and chunks
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  content TEXT NOT NULL,
  url TEXT NOT NULL,
  heading TEXT,
  chunk_index INTEGER DEFAULT 0,
  source VARCHAR(100) DEFAULT 'website',
  tokens INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP
);

CREATE INDEX idx_documents_source ON documents(source);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_documents_url ON documents(url);

-- Leads Table
-- Stores student inquiries and contact information
CREATE TABLE IF NOT EXISTS leads (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  phone VARCHAR(20),
  interest TEXT,
  source VARCHAR(100) DEFAULT 'chatbot',
  lead_score FLOAT DEFAULT 0.5,
  status VARCHAR(50) DEFAULT 'new',
  last_contact TIMESTAMP,
  salesforce_id VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_created_at ON leads(created_at);
CREATE INDEX idx_leads_score ON leads(lead_score DESC);

-- Chat Logs Table
-- Tracks all chat interactions for analytics
CREATE TABLE IF NOT EXISTS chat_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  query TEXT NOT NULL,
  response TEXT NOT NULL,
  session_id VARCHAR(255) NOT NULL,
  user_email VARCHAR(255),
  confidence_score FLOAT,
  processing_time_ms INTEGER,
  is_fallback BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_logs_session ON chat_logs(session_id);
CREATE INDEX idx_chat_logs_email ON chat_logs(user_email);
CREATE INDEX idx_chat_logs_created_at ON chat_logs(created_at);

-- Analytics Views

-- View: Top questions asked
CREATE OR REPLACE VIEW analytics_top_questions AS
SELECT 
  query,
  COUNT(*) as count,
  AVG(confidence_score) as avg_confidence,
  SUM(CASE WHEN is_fallback THEN 1 ELSE 0 END) as fallback_count
FROM chat_logs
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY query
ORDER BY count DESC
LIMIT 20;

-- View: Chat success rate
CREATE OR REPLACE VIEW analytics_success_rate AS
SELECT 
  DATE(created_at) as date,
  COUNT(*) as total_queries,
  SUM(CASE WHEN confidence_score >= 0.7 THEN 1 ELSE 0 END) as confident_queries,
  ROUND(100.0 * SUM(CASE WHEN confidence_score >= 0.7 THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM chat_logs
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- View: Lead generation metrics
CREATE OR REPLACE VIEW analytics_leads_daily AS
SELECT 
  DATE(created_at) as date,
  COUNT(*) as new_leads,
  SUM(CASE WHEN status = 'qualified' THEN 1 ELSE 0 END) as qualified_leads,
  AVG(lead_score) as avg_score
FROM leads
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Row Level Security (Optional - Enable if needed)
-- ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE chat_logs ENABLE ROW LEVEL SECURITY;

-- Sample Data (for testing)
-- INSERT INTO documents (content, url, heading, source) VALUES
-- ('Sample content about AIMS', 'https://theaims.ac.in', 'About AIMS', 'website')
-- ON CONFLICT DO NOTHING;
