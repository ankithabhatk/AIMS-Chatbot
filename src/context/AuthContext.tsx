"use client";

import { createContext, useContext, useState, ReactNode, Context } from 'react';
import { AuthState, LoginCredentials, SignupData, AuthResponse } from '../types/auth';

const AUTH_STORAGE_KEY = 'aims_auth';

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<boolean>;
  signup: (data: SignupData) => Promise<boolean>;
  logout: () => void;
}

const defaultValue: AuthContextType = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => false,
  signup: async () => false,
  logout: () => {},
};

export const AuthContext: Context<AuthContextType> = createContext<AuthContextType>(defaultValue);

const getInitialAuthState = (): AuthState => {
  if (typeof window === 'undefined') {
    return {
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    };
  }

  const stored = localStorage.getItem(AUTH_STORAGE_KEY);
  if (!stored) {
    return {
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    };
  }

  try {
    const authData = JSON.parse(stored);
    return {
      user: authData.user,
      token: authData.token,
      isAuthenticated: Boolean(authData.user && authData.token),
      isLoading: false,
    };
  } catch {
    return {
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    };
  }
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(getInitialAuthState);

  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });

      const data: AuthResponse = await response.json();

      if (data.success && data.user && data.token) {
        const newState = {
          user: data.user,
          token: data.token,
          isAuthenticated: true,
          isLoading: false,
        };
        setState(newState);
        localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(newState));
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const signup = async (data: SignupData): Promise<boolean> => {
    try {
      const response = await fetch('/api/v1/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const result: AuthResponse = await response.json();
      return result.success;
    } catch (error) {
      console.error('Signup error:', error);
      return false;
    }
  };

  const logout = () => {
    setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
    localStorage.removeItem(AUTH_STORAGE_KEY);
  };

  const value: AuthContextType = {
    ...state,
    login,
    signup,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
