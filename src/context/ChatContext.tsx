"use client";

import React, { createContext, useContext, useState, ReactNode, useEffect, useCallback } from 'react';
import { fetchChatResponse } from '../services/api';
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
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  restartSession: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

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
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  // Initial load
  useEffect(() => {
    const loadedColorTheme = localStorage.getItem('aims_theme') as 'light' | 'dark';
    if (loadedColorTheme) {
      setTheme(loadedColorTheme);
    }

    const loaded = loadConversations();
    setConversations(loaded);
    if (loaded.length > 0) {
      setCurrentConversationId(loaded[0].id);
      setMessages(loaded[0].messages);
    }

    const savedProfile = loadProfile();
    if (savedProfile) {
      setProfileState(savedProfile);
    }
  }, []);

  // Theme support
  useEffect(() => {
    if (theme === 'dark') {
      document.body.classList.add('dark');
    } else {
      document.body.classList.remove('dark');
    }
    localStorage.setItem('aims_theme', theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  }, []);

  // Sync to storage on conversations change
  useEffect(() => {
    if (conversations.length > 0) {
      saveConversations(conversations);
    }
  }, [conversations]);

  const saveProfile = useCallback((details: Omit<UserProfile, 'joinedAt'>) => {
    const fullProfile: UserProfile = {
      ...details,
      joinedAt: Date.now()
    };
    setProfileState(fullProfile);
    saveProfileStorage(fullProfile);
  }, []);

  const switchConversation = useCallback((id: string) => {
    const conv = conversations.find(c => c.id === id);
    if (conv) {
      setCurrentConversationId(id);
      setMessages(conv.messages);
    }
  }, [conversations]);

  const startNewConversation = useCallback(() => {
    setCurrentConversationId(null);
    setMessages([]);
  }, []);

  const deleteConversation = useCallback((id: string) => {
    setConversations(prev => {
      const filtered = prev.filter(c => c.id !== id);
      saveConversations(filtered);

      // If we are deleting the active conversation
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
      const updated = prev.map(c => c.id === id ? { ...c, title: newTitle } : c);
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
      // Derive title from first user message
      const title = isFromForm ? 'Onboarding' : trimmedQuery.slice(0, 35) + (trimmedQuery.length > 35 ? '...' : '');
      const newConv: Conversation = {
        id: activeId,
        title,
        messages: newMessages,
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      updatedConversations = [newConv, ...updatedConversations];
      setCurrentConversationId(activeId);
      setConversations(updatedConversations);
    } else {
      updatedConversations = updatedConversations.map(c =>
        c.id === activeId ? { ...c, messages: newMessages, updatedAt: Date.now() } : c
      );
      setConversations(updatedConversations);
    }

    try {
      let botContent = '';
      let isFallback = false;

      if (isFromForm) {
        const nameToUse = onboardingName || (profile ? profile.name.split(' ')[0] : 'there');
        botContent = `Thank you, ${nameToUse}. How can I assist you today?`;
      } else {
        const data = await fetchChatResponse(trimmedQuery, activeId);
        botContent = data.answer || data.message || 'Information currently unavailable. Please contact the admissions office directly.';
        isFallback = data.fallback === true;
      }

      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: botContent,
        isUser: false,
        isError: isFallback,
      };

      const finalMessages = [...newMessages, botMessage];
      setMessages(finalMessages);

      setConversations(prev => {
        const next = prev.map(c => c.id === activeId ? { ...c, messages: finalMessages, updatedAt: Date.now() } : c);
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
        const next = prev.map(c => c.id === activeId ? { ...c, messages: finalErrMessages, updatedAt: Date.now() } : c);
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
      toggleTheme,
      restartSession
    }}>
      {children}
    </ChatContext.Provider>
  );
};
