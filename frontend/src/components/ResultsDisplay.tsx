'use client';

import { useTranslation } from '@/hooks/useTranslation';
import { PostalCodeSearchResponse } from '@/types/api';
import { ExclamationTriangleIcon, ClockIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';

interface ResultsDisplayProps {
  results: PostalCodeSearchResponse | null;
  isLoading: boolean;
  error: string | null;
}

export default function ResultsDisplay({ results, isLoading, error }: ResultsDisplayProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center space-x-3 py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          <span className="text-gray-600 dark:text-gray-400">{t('loading')}</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex items-center space-x-3 text-red-600 dark:text-red-400">
          <ExclamationTriangleIcon className="w-5 h-5" />
          <span className="font-medium">{error}</span>
        </div>
      </div>
    );
  }

  if (!results) {
    return null;
  }

  const { results: records, count, fallback_applied, search_terms_used, performance } = results;

  if (count === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="text-center py-8">
          <MagnifyingGlassIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            {t('results.noResults')}
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Try adjusting your search criteria
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {t('results.title')}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {t('results.count', { count })}
            </p>
          </div>

          {/* Performance Metrics */}
          {performance && (
            <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
              <div className="flex items-center space-x-1">
                <ClockIcon className="w-4 h-4" />
                <span>{performance.response_time_ms}ms</span>
              </div>
            </div>
          )}
        </div>

        {/* Fallback Warning */}
        {fallback_applied && (
          <div className="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
            <div className="flex items-center space-x-2">
              <ExclamationTriangleIcon className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
              <span className="text-sm font-medium text-yellow-700 dark:text-yellow-300">
                {t('results.fallback')}
              </span>
            </div>
            <p className="text-sm text-yellow-600 dark:text-yellow-400 mt-1">
              {t('results.fallbackInfo')}
            </p>
          </div>
        )}
      </div>

      {/* Results Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('results.postalCode')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('results.city')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('results.street')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('results.houseNumbers')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('results.province')}
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {records.map((record, index) => (
              <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm font-mono font-medium text-blue-600 dark:text-blue-400">
                    {record.postal_code}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-900 dark:text-white">
                    {record.city}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {record.street || '-'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-600 dark:text-gray-400 font-mono">
                    {record.house_numbers || '-'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {record.province}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer with Additional Info */}
      {(search_terms_used || performance) && (
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
          <div className="flex flex-wrap items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            {search_terms_used && (
              <div className="flex flex-wrap gap-2">
                <span>Search terms:</span>
                {Object.entries(search_terms_used)
                  .filter(([_, value]) => value)
                  .map(([key, value]) => (
                    <span key={key} className="bg-gray-200 dark:bg-gray-600 px-2 py-1 rounded">
                      {key}: {value}
                    </span>
                  ))}
              </div>
            )}
            {performance && (
              <div className="flex items-center space-x-4">
                <span>{t('performance.responseTime', { time: performance.response_time_ms })}</span>
                <span>{t('performance.recordsSearched', { count: performance.records_searched })}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}