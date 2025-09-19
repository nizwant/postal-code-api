'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ApiClient, API_ENDPOINTS } from '@/lib/api';
import { ApiEndpoint } from '@/types/api';

interface AppContextType {
  // API Management
  currentApi: ApiEndpoint;
  apiEndpoints: ApiEndpoint[];
  apiClient: ApiClient;
  switchApi: (endpoint: ApiEndpoint) => void;
  checkApiHealth: (endpoint: ApiEndpoint) => Promise<void>;

  // Theme Management
  theme: 'light' | 'dark';
  toggleTheme: () => void;

  // Language Management
  language: 'pl' | 'en';
  setLanguage: (lang: 'pl' | 'en') => void;

  // UI State
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [currentApi, setCurrentApi] = useState<ApiEndpoint>(API_ENDPOINTS[0]);
  const [apiEndpoints, setApiEndpoints] = useState<ApiEndpoint[]>(API_ENDPOINTS);
  const [apiClient, setApiClient] = useState<ApiClient>(new ApiClient(API_ENDPOINTS[0].url));
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [language, setLanguage] = useState<'pl' | 'en'>('pl');
  const [isLoading, setIsLoading] = useState(false);

  // Initialize theme from localStorage or system preference
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
    if (savedTheme) {
      setTheme(savedTheme);
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setTheme(prefersDark ? 'dark' : 'light');
    }
  }, []);

  // Initialize language from localStorage
  useEffect(() => {
    const savedLanguage = localStorage.getItem('language') as 'pl' | 'en' | null;
    if (savedLanguage) {
      setLanguage(savedLanguage);
    }
  }, []);

  // Apply theme to document
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Save language preference
  useEffect(() => {
    localStorage.setItem('language', language);
  }, [language]);

  // Check all API endpoints health on mount
  useEffect(() => {
    const checkAllApis = async () => {
      const updatedEndpoints = await Promise.all(
        API_ENDPOINTS.map(async (endpoint) => {
          try {
            const client = new ApiClient(endpoint.url);
            const health = await client.healthCheck();
            return {
              ...endpoint,
              status: 'online' as const,
              responseTime: health.responseTime,
            };
          } catch (error) {
            return {
              ...endpoint,
              status: 'offline' as const,
              responseTime: undefined,
            };
          }
        })
      );
      setApiEndpoints(updatedEndpoints);
    };

    checkAllApis();
  }, []);

  const switchApi = (endpoint: ApiEndpoint) => {
    setCurrentApi(endpoint);
    setApiClient(new ApiClient(endpoint.url));
  };

  const checkApiHealth = async (endpoint: ApiEndpoint) => {
    try {
      const client = new ApiClient(endpoint.url);
      const health = await client.healthCheck();

      setApiEndpoints((prev) =>
        prev.map((api) =>
          api.port === endpoint.port
            ? { ...api, status: 'online', responseTime: health.responseTime }
            : api
        )
      );
    } catch (error) {
      setApiEndpoints((prev) =>
        prev.map((api) =>
          api.port === endpoint.port
            ? { ...api, status: 'offline', responseTime: undefined }
            : api
        )
      );
    }
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const value: AppContextType = {
    currentApi,
    apiEndpoints,
    apiClient,
    switchApi,
    checkApiHealth,
    theme,
    toggleTheme,
    language,
    setLanguage,
    isLoading,
    setIsLoading,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}