'use client';

import { useState } from 'react';
import { useApp } from '@/contexts/AppContext';
import { useTranslation } from '@/hooks/useTranslation';
import { SearchForm, PostalCodeForm, PostalCodeSearchResponse } from '@/types/api';

import Header from '@/components/Header';
import AddressForm from '@/components/AddressForm';
import PostalCodeForm from '@/components/PostalCodeForm';
import ResultsDisplay from '@/components/ResultsDisplay';

export default function Home() {
  const { apiClient, setIsLoading } = useApp();
  const { t } = useTranslation();

  const [results, setResults] = useState<PostalCodeSearchResponse | null>(null);
  const [isLoading, setLoadingLocal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoading = (loading: boolean) => {
    setLoadingLocal(loading);
    setIsLoading(loading);
  };

  const handleAddressSearch = async (form: SearchForm) => {
    handleLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await apiClient.searchPostalCodes({
        city: form.city || undefined,
        street: form.street || undefined,
        house_number: form.house_number || undefined,
        province: form.province || undefined,
        county: form.county || undefined,
        municipality: form.municipality || undefined,
        limit: 100,
      });

      setResults(response);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('errors.generic');
      setError(errorMessage);
    } finally {
      handleLoading(false);
    }
  };

  const handlePostalCodeSearch = async (form: PostalCodeForm) => {
    handleLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await apiClient.getPostalCodeDetails(form.postal_code);
      setResults(response);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('errors.generic');
      setError(errorMessage);
    } finally {
      handleLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Search Forms */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
            {/* Address to Postal Code */}
            <div>
              <AddressForm onSubmit={handleAddressSearch} isLoading={isLoading} />
            </div>

            {/* Postal Code to Addresses */}
            <div>
              <PostalCodeForm onSubmit={handlePostalCodeSearch} isLoading={isLoading} />
            </div>
          </div>

          {/* Results */}
          {(results || isLoading || error) && (
            <div>
              <ResultsDisplay results={results} isLoading={isLoading} error={error} />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}