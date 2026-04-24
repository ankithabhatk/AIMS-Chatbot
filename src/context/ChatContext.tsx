"use client";

import React, { createContext, useContext, useState, ReactNode, useEffect, useCallback, startTransition } from 'react';
import { fetchChatResponse, fetchPersistedConversations, LEADS_URL, PersistedConversation } from '../services/api';
import { loadConversations, saveConversations, Conversation, UserProfile, loadProfile, saveProfile as saveProfileStorage } from '../services/storageService';

export interface ChatMessage {
  id: string;
  content: string;
  isUser: boolean;
  isError?: boolean;
  metadata?: {
    confidence?: number;
    sources?: Array<{ url: string; title: string }>;
    suggestions?: string[];
  };
}

interface ChatContextType {
  conversations: Conversation[];
  currentConversationId: string | null;
  messages: ChatMessage[];
  isLoading: boolean;
  profile: UserProfile | null;
  sendMessage: (query: string, isFromForm?: boolean, onboardingName?: string) => Promise<void>;
  switchConversation: (id: string) => void;
  startNewConversation: () => void;
  deleteConversation: (id: string) => void;
  renameConversation: (id: string, newTitle: string) => void;
  saveProfile: (details: Omit<UserProfile, 'joinedAt'>) => void;
  theme: 'light' | 'dark' | 'high-contrast';
  setThemeMode: (mode: 'light' | 'dark' | 'high-contrast') => void;
  isChatOpen: boolean;
  setIsChatOpen: (isOpen: boolean) => void;
  isSidebarOpen: boolean;
  setIsSidebarOpen: (isOpen: boolean) => void;
  restartSession: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

const toTimestamp = (value?: string | number): number => {
  if (typeof value === 'number') return value;
  if (!value) return Date.now();
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? Date.now() : parsed;
};

const mapPersistedConversation = (conversation: PersistedConversation): Conversation => ({
  id: conversation.id,
  title: conversation.title || 'Conversation',
  createdAt: toTimestamp(conversation.created_at),
  updatedAt: toTimestamp(conversation.updated_at),
  messages: (conversation.messages || []).map(message => ({
    id: message.id,
    content: message.content,
    isUser: message.role === 'user',
    isError: message.role === 'assistant' ? message.fallback === true : false,
    metadata: message.role === 'assistant'
      ? {
          confidence: message.confidence,
          sources: message.sources,
          suggestions: message.suggestions,
        }
      : undefined,
  })),
});

const mergeConversations = (local: Conversation[], remote: Conversation[]): Conversation[] => {
  const merged = new Map<string, Conversation>();

  for (const conversation of local) {
    merged.set(conversation.id, conversation);
  }

  for (const conversation of remote) {
    const existing = merged.get(conversation.id);
    if (!existing || conversation.updatedAt >= existing.updatedAt || conversation.messages.length >= existing.messages.length) {
      merged.set(conversation.id, conversation);
    }
  }

  return Array.from(merged.values()).sort((a, b) => b.updatedAt - a.updatedAt);
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) throw new Error('useChat must be used within a ChatProvider');
  return context;
};

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [profile, setProfileState] = useState<UserProfile | null>(null);
  const [theme, setTheme] = useState<'light' | 'dark' | 'high-contrast'>('light');
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    const loadedColorTheme = localStorage.getItem('aims_theme') as any;
    const themes = ['light', 'dark', 'high-contrast'];
    if (loadedColorTheme && themes.includes(loadedColorTheme)) {
      setTheme(loadedColorTheme);
    } else {
      setTheme('light');
    }

    const loadedConversations = loadConversations();
    setConversations(loadedConversations);
    if (loadedConversations.length > 0) {
      setCurrentConversationId(loadedConversations[0].id);
      setMessages(loadedConversations[0].messages);
    }

    const savedProfile = loadProfile();
    if (savedProfile) {
      setProfileState(savedProfile);
    }
  }, []);

  useEffect(() => {
    document.body.classList.remove('light', 'dark', 'high-contrast');
    document.body.classList.add(theme);
    localStorage.setItem('aims_theme', theme);
  }, [theme]);

  useEffect(() => {
    if (!profile?.email) return;

    let cancelled = false;

    const hydratePersistedHistory = async () => {
      const remoteConversations = await fetchPersistedConversations(profile.email);
      if (cancelled || remoteConversations.length === 0) {
        return;
      }

      const merged = mergeConversations(
        loadConversations(),
        remoteConversations.map(mapPersistedConversation)
      );

      startTransition(() => {
        setConversations(merged);
        const preferredId =
          currentConversationId && merged.some(conversation => conversation.id === currentConversationId)
            ? currentConversationId
            : merged[0]?.id ?? null;
        setCurrentConversationId(preferredId);
        const activeConversation = merged.find(conversation => conversation.id === preferredId);
        setMessages(activeConversation ? activeConversation.messages : []);
      });
    };

    hydratePersistedHistory();
    return () => {
      cancelled = true;
    };
  }, [profile?.email]);

  const setThemeMode = useCallback((mode: 'light' | 'dark' | 'high-contrast') => {
    setTheme(mode);
  }, []);

  useEffect(() => {
    if (conversations.length > 0) {
      saveConversations(conversations);
    }
  }, [conversations]);

  const captureLead = async (userProfile: UserProfile, sessionId: string) => {
    try {
      const names = userProfile.name.split(' ');
      const firstName = names[0];
      const lastName = names.slice(1).join(' ') || 'Student';
      
      await fetch(LEADS_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          first_name: firstName,
          last_name: lastName,
          email: userProfile.email,
          phone: userProfile.mobile,
          interested_programs: [userProfile.course]
        })
      });
    } catch (error) {
      console.error('Lead capture failed:', error);
    }
  };

  const saveProfile = useCallback((details: Omit<UserProfile, 'joinedAt'>) => {
    const fullProfile: UserProfile = {
      ...details,
      joinedAt: Date.now()
    };
    setProfileState(fullProfile);
    saveProfileStorage(fullProfile);
    
    if (currentConversationId) {
      captureLead(fullProfile, currentConversationId);
    }
  }, [currentConversationId]);

  const switchConversation = useCallback((id: string) => {
    const conversation = conversations.find(item => item.id === id);
    if (conversation) {
      setCurrentConversationId(id);
      setMessages(conversation.messages);
    }
  }, [conversations]);

  const startNewConversation = useCallback(() => {
    setCurrentConversationId(null);
    setMessages([]);
  }, []);

  const deleteConversation = useCallback((id: string) => {
    setConversations(prev => {
      const filtered = prev.filter(conversation => conversation.id !== id);
      saveConversations(filtered);

      if (currentConversationId === id) {
        if (filtered.length > 0) {
          setCurrentConversationId(filtered[0].id);
          setMessages(filtered[0].messages);
        } else {
          setCurrentConversationId(null);
          setMessages([]);
        }
      }
      return filtered;
    });
  }, [currentConversationId]);

  const renameConversation = useCallback((id: string, newTitle: string) => {
    setConversations(prev => {
      const updated = prev.map(conversation => conversation.id === id ? { ...conversation, title: newTitle } : conversation);
      saveConversations(updated);
      return updated;
    });
  }, []);

  const sendMessage = async (query: string, isFromForm = false, onboardingName?: string) => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: trimmedQuery,
      isUser: true,
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setIsLoading(true);

    let activeId = currentConversationId;
    let updatedConversations = [...conversations];

    if (!activeId) {
      activeId = 'conv_' + Date.now().toString();
      const title = isFromForm ? 'Onboarding' : trimmedQuery.slice(0, 35) + (trimmedQuery.length > 35 ? '...' : '');
      const newConversation: Conversation = {
        id: activeId,
        title,
        messages: newMessages,
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      updatedConversations = [newConversation, ...updatedConversations];
      setCurrentConversationId(activeId);
      setConversations(updatedConversations);
    } else {
      updatedConversations = updatedConversations.map(conversation =>
        conversation.id === activeId ? { ...conversation, messages: newMessages, updatedAt: Date.now() } : conversation
      );
      setConversations(updatedConversations);
    }

    try {
      let botContent = '';
      let isFallback = false;
      let metadata: ChatMessage['metadata'] | undefined;

      if (isFromForm) {
        const nameToUse = onboardingName || (profile ? profile.name.split(' ')[0] : 'there');
        botContent = `Thank you, ${nameToUse}. How can I assist you today?`;
      } else {
        const data = await fetchChatResponse(
          trimmedQuery,
          activeId,
          profile ? { name: profile.name, email: profile.email, phone: profile.mobile } : undefined
        );
        botContent = data.answer || data.message || 'Information currently unavailable. Please contact the admissions office directly.';
        isFallback = data.fallback === true;
        metadata = {
          confidence: data.confidence,
          sources: data.sources,
          suggestions: data.suggestions,
        };
      }

      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: botContent,
        isUser: false,
        isError: isFallback,
        metadata,
      };

      const finalMessages = [...newMessages, botMessage];
      setMessages(finalMessages);

      setConversations(prev => {
        const next = prev.map(conversation =>
          conversation.id === activeId ? { ...conversation, messages: finalMessages, updatedAt: Date.now() } : conversation
        );
        saveConversations(next);
        return next;
      });

    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: 'System Error: Unable to communicate with the academic knowledge base at this time.',
        isUser: false,
        isError: true,
      };
      const finalErrMessages = [...newMessages, errorMessage];
      setMessages(finalErrMessages);

      setConversations(prev => {
        const next = prev.map(conversation =>
          conversation.id === activeId ? { ...conversation, messages: finalErrMessages, updatedAt: Date.now() } : conversation
        );
        saveConversations(next);
        return next;
      });

    } finally {
      setIsLoading(false);
    }
  };

  const restartSession = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('aims_user_profile');
      localStorage.removeItem('aims_conversations');
    }
    setProfileState(null);
    setConversations([]);
    setMessages([]);
    setCurrentConversationId(null);
  }, []);

  return (
    <ChatContext.Provider value={{
      conversations,
      currentConversationId,
      messages,
      isLoading,
      profile,
      sendMessage,
      switchConversation,
      startNewConversation,
      deleteConversation,
      renameConversation,
      saveProfile,
      theme,
      setThemeMode,
      isChatOpen,
      setIsChatOpen,
      isSidebarOpen,
      setIsSidebarOpen,
      restartSession
    }}>
      {children}
    </ChatContext.Provider>
  );
};
