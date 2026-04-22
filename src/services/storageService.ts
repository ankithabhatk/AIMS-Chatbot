import { ChatMessage } from '../context/ChatContext';

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

export interface UserProfile {
  name: string;
  mobile: string;
  email: string;
  course: string;
  joinedAt: number;
}

const STORAGE_KEY = 'aims_conversations';
const PROFILE_KEY = 'aims_user_profile';
const EXPIRY_DAYS = 30;
const MS_PER_DAY = 24 * 60 * 60 * 1000;
const MAX_CONVERSATIONS = 20;

export const loadConversations = (): Conversation[] => {
  if (typeof window === 'undefined') return [];
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    if (!data) return [];
    
    let conversations: Conversation[] = JSON.parse(data);
    const now = Date.now();
    
    // Filter out conversations older than 30 days
    const validConversations = conversations.filter(conv => {
      const ageDays = (now - conv.updatedAt) / MS_PER_DAY;
      return ageDays <= EXPIRY_DAYS;
    });

    if (validConversations.length !== conversations.length) {
      saveConversations(validConversations);
    }
    
    return validConversations.sort((a, b) => b.updatedAt - a.updatedAt);
  } catch (error) {
    console.error("Failed to load conversations:", error);
    return [];
  }
};

export const saveConversations = (conversations: Conversation[]) => {
  if (typeof window === 'undefined') return;
  try {
    const limited = conversations
      .sort((a, b) => b.updatedAt - a.updatedAt)
      .slice(0, MAX_CONVERSATIONS);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(limited));
  } catch (error) {
    console.error("Failed to save conversations:", error);
  }
};

export const loadProfile = (): UserProfile | null => {
  if (typeof window === 'undefined') return null;
  try {
    const data = localStorage.getItem(PROFILE_KEY);
    if (!data) return null;
    return JSON.parse(data);
  } catch (error) {
    console.error("Failed to load profile:", error);
    return null;
  }
};

export const saveProfile = (profile: UserProfile | null) => {
  if (typeof window === 'undefined') return;
  try {
    if (profile) {
      localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
    } else {
      localStorage.removeItem(PROFILE_KEY);
    }
  } catch (error) {
    console.error("Failed to save profile:", error);
  }
};
