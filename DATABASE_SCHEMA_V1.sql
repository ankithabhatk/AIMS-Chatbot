-- Business Layer Schema v1

-- 1. Leads table for capturing conversational inputs
CREATE TABLE IF NOT EXISTS leads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text,
  phone text,
  email text,
  interest text,
  source text DEFAULT 'chatbot',
  created_at timestamp DEFAULT now()
);

-- 2. Chat logs for analytics and engagement scoring
CREATE TABLE IF NOT EXISTS chat_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id text,
  user_query text,
  bot_response text,
  confidence_score float,
  processing_time_ms int,
  is_fallback bool DEFAULT false,
  created_at timestamp DEFAULT now()
);
