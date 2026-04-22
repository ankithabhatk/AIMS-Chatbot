export const API_URL = 'http://127.0.0.1:8000/api/v1/chat';

export interface ChatResponse {
  answer?: string;
  message?: string;
  confidence?: number;
  sources?: Array<{ url: string; title: string }>;
  suggestions?: string[];
  fallback?: boolean;
}

export const fetchChatResponse = async (query: string, sessionId: string): Promise<ChatResponse> => {
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, session_id: sessionId })
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
