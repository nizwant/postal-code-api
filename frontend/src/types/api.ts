export interface PostalCodeRecord {
  postal_code: string;
  city: string;
  street?: string;
  house_numbers?: string;
  municipality?: string;
  county?: string;
  province: string;
}

export interface PostalCodeSearchResponse {
  results: PostalCodeRecord[];
  count: number;
  fallback_applied?: boolean;
  search_terms_used: {
    city?: string;
    street?: string;
    house_number?: string;
    province?: string;
    county?: string;
    municipality?: string;
  };
  performance?: {
    response_time_ms: number;
    records_searched: number;
  };
}

export interface LocationOption {
  name: string;
  count?: number;
}

export interface LocationResponse {
  results: LocationOption[];
  count: number;
}

export interface ApiEndpoint {
  name: string;
  url: string;
  port: number;
  status: 'online' | 'offline' | 'checking';
  responseTime?: number;
}

export interface SearchForm {
  city: string;
  street: string;
  house_number: string;
  province: string;
  county: string;
  municipality: string;
}

export interface PostalCodeForm {
  postal_code: string;
}