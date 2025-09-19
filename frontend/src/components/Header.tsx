'use client';

import { useApp } from '@/contexts/AppContext';
import { useTranslation } from '@/hooks/useTranslation';
import { SunIcon, MoonIcon, GlobeAltIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { useState } from 'react';

export default function Header() {
  const { theme, toggleTheme, language, setLanguage, currentApi, apiEndpoints, switchApi } = useApp();
  const { t } = useTranslation();
  const [showApiDropdown, setShowApiDropdown] = useState(false);
  const [showLangDropdown, setShowLangDropdown] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'text-green-500';
      case 'offline':
        return 'text-red-500';
      default:
        return 'text-yellow-500';
    }
  };

  return (
    <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Title */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                {t('nav.title')}
              </h1>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center space-x-4">
            {/* API Selector */}
            <div className="relative">
              <button
                onClick={() => setShowApiDropdown(!showApiDropdown)}
                className="flex items-center space-x-2 px-3 py-2 rounded-md bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              >
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {currentApi.name}
                </span>
                <div className={`w-2 h-2 rounded-full ${getStatusColor(currentApi.status)}`} />
                <ChevronDownIcon className="w-4 h-4 text-gray-500" />
              </button>

              {showApiDropdown && (
                <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-md shadow-lg z-10 border border-gray-200 dark:border-gray-700">
                  <div className="py-1">
                    {apiEndpoints.map((api) => (
                      <button
                        key={api.port}
                        onClick={() => {
                          switchApi(api);
                          setShowApiDropdown(false);
                        }}
                        className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center justify-between ${
                          currentApi.port === api.port ? 'bg-blue-50 dark:bg-blue-900' : ''
                        }`}
                      >
                        <div className="flex items-center space-x-2">
                          <span className="font-medium text-gray-900 dark:text-white">
                            {api.name}
                          </span>
                          <span className="text-xs text-gray-500">:{api.port}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          {api.responseTime && (
                            <span className="text-xs text-gray-500">
                              {api.responseTime}ms
                            </span>
                          )}
                          <div className={`w-2 h-2 rounded-full ${getStatusColor(api.status)}`} />
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Language Selector */}
            <div className="relative">
              <button
                onClick={() => setShowLangDropdown(!showLangDropdown)}
                className="flex items-center space-x-1 px-3 py-2 rounded-md bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                title={t('nav.language')}
              >
                <GlobeAltIcon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300 uppercase">
                  {language}
                </span>
                <ChevronDownIcon className="w-4 h-4 text-gray-500" />
              </button>

              {showLangDropdown && (
                <div className="absolute right-0 mt-2 w-24 bg-white dark:bg-gray-800 rounded-md shadow-lg z-10 border border-gray-200 dark:border-gray-700">
                  <div className="py-1">
                    <button
                      onClick={() => {
                        setLanguage('pl');
                        setShowLangDropdown(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 ${
                        language === 'pl' ? 'bg-blue-50 dark:bg-blue-900 text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      Polski
                    </button>
                    <button
                      onClick={() => {
                        setLanguage('en');
                        setShowLangDropdown(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 ${
                        language === 'en' ? 'bg-blue-50 dark:bg-blue-900 text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      English
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-md bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title={t('nav.theme')}
            >
              {theme === 'light' ? (
                <MoonIcon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              ) : (
                <SunIcon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              )}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}