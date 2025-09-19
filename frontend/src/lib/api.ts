import { ApiEndpoint, PostalCodeSearchResponse, LocationResponse } from '@/types/api';

export const API_ENDPOINTS: ApiEndpoint[] = [
  { name: 'Flask', url: 'http://localhost:5001', port: 5001, status: 'checking' },
  { name: 'FastAPI', url: 'http://localhost:5002', port: 5002, status: 'checking' },
  { name: 'Go', url: 'http://localhost:5003', port: 5003, status: 'checking' },
  { name: 'Elixir', url: 'http://localhost:5004', port: 5004, status: 'checking' },
];

export class ApiClient {
  private baseUrl: string;
  private port: string;
  private abortController: AbortController | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.port = new URL(baseUrl).port;
  }

  private getProxyUrl(path: string): string {
    // Use proxy in browser environment to handle CORS
    if (typeof window !== 'undefined') {
      const separator = path.includes('?') ? '&' : '?';
      return `/api/proxy/${path}${separator}port=${this.port}`;
    }
    return `${this.baseUrl}/${path}`;
  }

  private async fetchWithTimeout(url: string, options: RequestInit = {}, timeout = 5000) {
    this.abortController = new AbortController();
    const timeoutId = setTimeout(() => this.abortController?.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: this.abortController.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  async healthCheck(): Promise<{ status: string; responseTime: number }> {
    const startTime = Date.now();
    try {
      const response = await this.fetchWithTimeout(this.getProxyUrl('health'));
      const responseTime = Date.now() - startTime;

      if (response.ok) {
        const data = await response.json();
        return { status: data.status, responseTime };
      }
      throw new Error(`HTTP ${response.status}`);
    } catch (error) {
      const responseTime = Date.now() - startTime;
      throw new Error(`Health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async searchPostalCodes(params: {
    city?: string;
    street?: string;
    house_number?: string;
    province?: string;
    county?: string;
    municipality?: string;
    limit?: number;
  }): Promise<PostalCodeSearchResponse> {
    const startTime = Date.now();
    const searchParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (typeof value === 'string' && value.trim()) {
          searchParams.append(key, value);
        } else if (typeof value === 'number') {
          searchParams.append(key, value.toString());
        }
      }
    });

    try {
      const response = await this.fetchWithTimeout(
        this.getProxyUrl(`postal-codes?${searchParams.toString()}`)
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const responseTime = Date.now() - startTime;

      return {
        ...data,
        performance: {
          response_time_ms: responseTime,
          records_searched: data.count || 0,
        },
      };
    } catch (error) {
      throw new Error(`Search failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getPostalCodeDetails(postalCode: string): Promise<PostalCodeSearchResponse> {
    const startTime = Date.now();
    try {
      const response = await this.fetchWithTimeout(this.getProxyUrl(`postal-codes/${postalCode}`));

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Postal code not found');
        }
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const responseTime = Date.now() - startTime;

      return {
        ...data,
        performance: {
          response_time_ms: responseTime,
          records_searched: data.count || 0,
        },
      };
    } catch (error) {
      throw new Error(`Lookup failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getProvinces(prefix?: string): Promise<LocationResponse> {
    const searchParams = new URLSearchParams();
    if (prefix?.trim()) {
      searchParams.append('prefix', prefix);
    }

    try {
      const response = await this.fetchWithTimeout(
        this.getProxyUrl(`locations/provinces?${searchParams.toString()}`)
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Failed to fetch provinces: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getCounties(province?: string, prefix?: string): Promise<LocationResponse> {
    const searchParams = new URLSearchParams();
    if (province?.trim()) searchParams.append('province', province);
    if (prefix?.trim()) searchParams.append('prefix', prefix);

    try {
      const response = await this.fetchWithTimeout(
        this.getProxyUrl(`locations/counties?${searchParams.toString()}`)
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Failed to fetch counties: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getMunicipalities(province?: string, county?: string, prefix?: string): Promise<LocationResponse> {
    const searchParams = new URLSearchParams();
    if (province?.trim()) searchParams.append('province', province);
    if (county?.trim()) searchParams.append('county', county);
    if (prefix?.trim()) searchParams.append('prefix', prefix);

    try {
      const response = await this.fetchWithTimeout(
        this.getProxyUrl(`locations/municipalities?${searchParams.toString()}`)
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Failed to fetch municipalities: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getCities(province?: string, county?: string, municipality?: string, prefix?: string): Promise<LocationResponse> {
    const searchParams = new URLSearchParams();
    if (province?.trim()) searchParams.append('province', province);
    if (county?.trim()) searchParams.append('county', county);
    if (municipality?.trim()) searchParams.append('municipality', municipality);
    if (prefix?.trim()) searchParams.append('prefix', prefix);

    try {
      const response = await this.fetchWithTimeout(
        this.getProxyUrl(`locations/cities?${searchParams.toString()}`)
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Failed to fetch cities: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getStreets(city?: string, province?: string, county?: string, municipality?: string, prefix?: string): Promise<LocationResponse> {
    const searchParams = new URLSearchParams();
    if (city?.trim()) searchParams.append('city', city);
    if (province?.trim()) searchParams.append('province', province);
    if (county?.trim()) searchParams.append('county', county);
    if (municipality?.trim()) searchParams.append('municipality', municipality);
    if (prefix?.trim()) searchParams.append('prefix', prefix);

    try {
      const response = await this.fetchWithTimeout(
        this.getProxyUrl(`locations/streets?${searchParams.toString()}`)
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Failed to fetch streets: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  cancel() {
    if (this.abortController) {
      this.abortController.abort();
    }
  }
}