const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

const normalizeBaseUrl = (value?: string): string => {
  const trimmed = value?.trim();
  if (!trimmed) {
    return DEFAULT_API_BASE_URL;
  }

  return trimmed.endsWith('/') ? trimmed.slice(0, -1) : trimmed;
};

export const API_BASE_URL = normalizeBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL);
export const API_URL = `${API_BASE_URL}/chat`;
export const LEADS_URL = `${API_BASE_URL}/leads`;

export interface SourceItem {
  url: string;
  title: string;
}

export interface ChatResponse {
  answer?: string;
  message?: string;
  confidence?: number;
  sources?: SourceItem[];
  suggestions?: string[];
  fallback?: boolean;
  status?: string;
  course?: string;
  intent?: string;
  meta?: Record<string, unknown> & {
    session_id?: string;
    corrected_query?: string;
    original_query?: string;
    response_time_ms?: number;
    cache_hit?: boolean;
  };
}

export interface ChatRequestUser {
  name?: string;
  email?: string;
  phone?: string;
}

export interface PersistedMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  confidence?: number;
  sources?: SourceItem[];
  suggestions?: string[];
  fallback?: boolean;
}

export interface PersistedConversation {
  id: string;
  title: string;
  user_email?: string;
  user_name?: string;
  created_at?: string;
  updated_at?: string;
  message_count?: number;
  active_course?: string;
  active_topic?: string;
  last_intent?: string;
  messages: PersistedMessage[];
}

export const fetchChatResponse = async (
  query: string,
  sessionId: string,
  user?: ChatRequestUser | null
): Promise<ChatResponse> => {
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        user: user || undefined,
        context: { session_id: sessionId },
        session_id: sessionId
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const fetchPersistedConversations = async (
  userEmail: string,
  limit = 20
): Promise<PersistedConversation[]> => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/chat/history?user_email=${encodeURIComponent(userEmail)}&limit=${limit}`
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    return Array.isArray(data.sessions) ? data.sessions : [];
  } catch (error) {
    console.error('Persisted history fetch failed:', error);
    return [];
  }
};
