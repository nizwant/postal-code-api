'use client';

import { useState, useEffect, useRef } from 'react';
import { useApp } from '@/contexts/AppContext';
import { useTranslation } from '@/hooks/useTranslation';
import { SearchForm, LocationOption } from '@/types/api';
import { MagnifyingGlassIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';

interface AddressFormProps {
  onSubmit: (form: SearchForm) => void;
  isLoading: boolean;
}

export default function AddressForm({ onSubmit, isLoading }: AddressFormProps) {
  const { apiClient } = useApp();
  const { t } = useTranslation();
  const [form, setForm] = useState<SearchForm>({
    city: '',
    street: '',
    house_number: '',
    province: '',
    county: '',
    municipality: '',
  });
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [suggestions, setSuggestions] = useState<{
    [key: string]: LocationOption[];
  }>({});
  const [activeSuggestion, setActiveSuggestion] = useState<string | null>(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState<{
    [key: string]: boolean;
  }>({});

  const debounceRefs = useRef<{ [key: string]: NodeJS.Timeout }>({});

  const handleInputChange = (field: keyof SearchForm, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));

    // Clear previous debounce timeout
    if (debounceRefs.current[field]) {
      clearTimeout(debounceRefs.current[field]);
    }

    // Only fetch suggestions for certain fields and when value is long enough
    const shouldFetchSuggestions = ['city', 'province', 'county', 'municipality'].includes(field) &&
                                   value.length >= 2;

    if (shouldFetchSuggestions) {
      setLoadingSuggestions(prev => ({ ...prev, [field]: true }));

      debounceRefs.current[field] = setTimeout(async () => {
        try {
          let response;
          switch (field) {
            case 'city':
              response = await apiClient.getCities(
                form.province || undefined,
                form.county || undefined,
                form.municipality || undefined,
                value
              );
              break;
            case 'province':
              response = await apiClient.getProvinces(value);
              break;
            case 'county':
              response = await apiClient.getCounties(form.province || undefined, value);
              break;
            case 'municipality':
              response = await apiClient.getMunicipalities(
                form.province || undefined,
                form.county || undefined,
                value
              );
              break;
            default:
              return;
          }

          // Extract the correct array based on the field type
          let items: string[] = [];
          switch (field) {
            case 'city':
              items = response.cities || [];
              break;
            case 'province':
              items = response.provinces || [];
              break;
            case 'county':
              items = response.counties || [];
              break;
            case 'municipality':
              items = response.municipalities || [];
              break;
          }

          const suggestions = items.slice(0, 10).map(name => ({ name }));
          setSuggestions(prev => ({
            ...prev,
            [field]: suggestions,
          }));
        } catch (error) {
          console.error(`Failed to fetch ${field} suggestions:`, error);
          setSuggestions(prev => ({ ...prev, [field]: [] }));
        } finally {
          setLoadingSuggestions(prev => ({ ...prev, [field]: false }));
        }
      }, 300);
    } else {
      setSuggestions(prev => ({ ...prev, [field]: [] }));
    }
  };

  const handleSuggestionClick = (field: keyof SearchForm, suggestion: LocationOption) => {
    setForm(prev => ({ ...prev, [field]: suggestion.name }));
    setSuggestions(prev => ({ ...prev, [field]: [] }));
    setActiveSuggestion(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  const handleClear = () => {
    setForm({
      city: '',
      street: '',
      house_number: '',
      province: '',
      county: '',
      municipality: '',
    });
    setSuggestions({});
  };

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (activeSuggestion) {
        setActiveSuggestion(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [activeSuggestion]);

  const renderInput = (
    field: keyof SearchForm,
    label: string,
    placeholder: string,
    required: boolean = false
  ) => {
    const fieldSuggestions = suggestions[field] || [];
    const isLoadingSuggestion = loadingSuggestions[field];
    const showSuggestions = activeSuggestion === field && fieldSuggestions.length > 0;

    return (
      <div className="space-y-1 relative">
        <label htmlFor={field} className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
          {!required && (
            <span className="text-gray-400 text-xs ml-1">{t('search.optional')}</span>
          )}
        </label>
        <div className="relative">
          <input
            id={field}
            type="text"
            value={form[field]}
            onChange={(e) => handleInputChange(field, e.target.value)}
            onFocus={() => setActiveSuggestion(field)}
            placeholder={placeholder}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white bg-white"
            disabled={isLoading}
          />
          {isLoadingSuggestion && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
            </div>
          )}
        </div>

        {showSuggestions && (
          <div className="absolute z-10 w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg max-h-48 overflow-y-auto">
            {fieldSuggestions.map((suggestion, index) => (
              <button
                key={index}
                type="button"
                onClick={() => handleSuggestionClick(field, suggestion)}
                className="w-full text-left px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 text-sm text-gray-900 dark:text-white flex justify-between items-center"
              >
                <span>{suggestion.name}</span>
                {suggestion.count && (
                  <span className="text-xs text-gray-500">({suggestion.count})</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          {t('search.title')}
        </h2>
        <p className="text-gray-600 dark:text-gray-400 text-sm">
          {t('search.subtitle')}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Main Fields */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {renderInput('city', t('search.city'), t('search.placeholder.city'), true)}
          {renderInput('street', t('search.street'), t('search.placeholder.street'), true)}
          {renderInput('house_number', t('search.houseNumber'), t('search.placeholder.houseNumber'), true)}
        </div>

        {/* Advanced Options Toggle */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center space-x-2 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
          >
            {showAdvanced ? (
              <ChevronUpIcon className="w-4 h-4" />
            ) : (
              <ChevronDownIcon className="w-4 h-4" />
            )}
            <span>
              {showAdvanced ? t('search.hideAdvanced') : t('search.showAdvanced')}
            </span>
          </button>
        </div>

        {/* Advanced Fields */}
        {showAdvanced && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            {renderInput('province', t('search.province'), t('search.placeholder.province'))}
            {renderInput('county', t('search.county'), t('search.placeholder.county'))}
            {renderInput('municipality', t('search.municipality'), t('search.placeholder.municipality'))}
          </div>
        )}


        {/* Buttons */}
        <div className="flex space-x-3">
          <button
            type="submit"
            disabled={isLoading}
            className="flex-1 flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md font-medium transition-colors"
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <MagnifyingGlassIcon className="w-4 h-4" />
            )}
            <span>{t('search.submit')}</span>
          </button>
          <button
            type="button"
            onClick={handleClear}
            disabled={isLoading}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            {t('search.clear')}
          </button>
        </div>
      </form>
    </div>
  );
}