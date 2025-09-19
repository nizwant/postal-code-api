'use client';

import { useState } from 'react';
import { useTranslation } from '@/hooks/useTranslation';
import { PostalCodeForm } from '@/types/api';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';

interface PostalCodeFormProps {
  onSubmit: (form: PostalCodeForm) => void;
  isLoading: boolean;
}

export default function PostalCodeForm({ onSubmit, isLoading }: PostalCodeFormProps) {
  const { t } = useTranslation();
  const [form, setForm] = useState<PostalCodeForm>({
    postal_code: '',
  });
  const [error, setError] = useState<string | null>(null);

  const validatePostalCode = (code: string): boolean => {
    // Polish postal code format: XX-XXX (2 digits, dash, 3 digits)
    const regex = /^\d{2}-\d{3}$/;
    return regex.test(code);
  };

  const handleInputChange = (value: string) => {
    // Auto-format: add dash after 2 digits
    let formatted = value.replace(/\D/g, ''); // Remove non-digits
    if (formatted.length > 2) {
      formatted = formatted.slice(0, 2) + '-' + formatted.slice(2, 5);
    }

    setForm({ postal_code: formatted });

    // Clear error when user types
    if (error) {
      setError(null);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!form.postal_code.trim()) {
      setError(t('errors.generic'));
      return;
    }

    if (!validatePostalCode(form.postal_code)) {
      setError(t('errors.invalidPostalCode'));
      return;
    }

    setError(null);
    onSubmit(form);
  };

  const handleClear = () => {
    setForm({ postal_code: '' });
    setError(null);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          {t('reverse.title')}
        </h2>
        <p className="text-gray-600 dark:text-gray-400 text-sm">
          {t('reverse.subtitle')}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1">
          <label htmlFor="postal_code" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            {t('reverse.postalCode')}
          </label>
          <input
            id="postal_code"
            type="text"
            value={form.postal_code}
            onChange={(e) => handleInputChange(e.target.value)}
            placeholder={t('reverse.placeholder')}
            maxLength={6}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white bg-white ${
              error
                ? 'border-red-300 dark:border-red-600'
                : 'border-gray-300 dark:border-gray-600'
            }`}
            disabled={isLoading}
          />
          {error && (
            <p className="text-sm text-red-600 dark:text-red-400 mt-1">
              {error}
            </p>
          )}
        </div>

        <div className="flex space-x-3">
          <button
            type="submit"
            disabled={isLoading || !form.postal_code.trim()}
            className="flex-1 flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md font-medium transition-colors"
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <MagnifyingGlassIcon className="w-4 h-4" />
            )}
            <span>{t('reverse.submit')}</span>
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