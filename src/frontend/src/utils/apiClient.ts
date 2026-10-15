import axios from 'axios';
// Type definitions for axios (since they're not exported in v1.6+)
type AxiosError<T = unknown> = {
  isAxiosError: boolean;
  message: string;
  response?: { data: T; status: number };
};
import { config, log } from './config';
import { isBrowser, getLocalStorage } from './env';

// Import antd message for toast notifications
import { message } from 'antd';

export interface NormalizedError {
  message: string;
  code: string | number;
  status?: number;
  details?: unknown;
  retryable: boolean;
  timestamp: string;
}

const normalizeError = (error: unknown): NormalizedError => {
  const timestamp = new Date().toISOString();

  if (
    error &&
    typeof error === 'object' &&
    'isAxiosError' in error &&
    (error as { isAxiosError: boolean }).isAxiosError
  ) {
    const axiosError = error as AxiosError<{ message?: string; code?: string; details?: unknown }>;

    if (!axiosError.response) {
      return {
        message: axiosError.message || 'Network error - please check connection',
        code: 'NETWORK_ERROR',
        retryable: true,
        timestamp,
      };
    }

    const status = axiosError.response.status;
    const data = axiosError.response.data as
      { message?: string; code?: string; details?: unknown } | undefined;

    return {
      message: data?.message || `Request failed with status ${status}`,
      code: data?.code || status,
      status,
      details: data?.details,
      retryable: status >= 500 || status === 408 || status === 429,
      timestamp,
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message,
      code: 'UNKNOWN_ERROR',
      retryable: false,
      timestamp,
    };
  }

  return {
    message: 'Unknown error occurred',
    code: 'UNKNOWN_ERROR',
    retryable: false,
    timestamp,
  };
};

const setDefaultHeaders = (instance: ReturnType<typeof axios.create>, token: string | null) => {
  if (token) {
    instance.defaults.headers.common['X-API-Key'] = token;
    instance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete instance.defaults.headers.common['X-API-Key'];
    delete instance.defaults.headers.common['Authorization'];
  }
};

const createApiClient = () => {
  // Ensure baseURL includes /api prefix (no v1)
  const baseURL = config.apiBaseUrl ? `${config.apiBaseUrl}/api/v1` : '/api/v1';

  const instance = axios.create({
    baseURL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Set initial token from env or localStorage
  const initialToken = (() => {
    const apiKey = import.meta.env.VITE_API_KEY;
    return apiKey && apiKey !== 'your_api_key_here' ? apiKey : null;
  })();
  setDefaultHeaders(instance, initialToken);

  instance.interceptors.request.use(
    (requestConfig) => {
      log('debug', `API Request: ${requestConfig.method?.toUpperCase()} ${requestConfig.url}`);
      return requestConfig;
    },
    (error) => {
      log('error', 'API Request Error:', error);
      return Promise.reject(normalizeError(error));
    },
  );

  instance.interceptors.response.use(
    (response) => {
      log('debug', `API Response: ${response.status} ${response.config.url}`);
      return response;
    },
    async (error) => {
      const normalizedError = normalizeError(error);
      log(
        'error',
        `API Error: ${normalizedError.code} - ${normalizedError.message}`,
        normalizedError,
      );

      // Handle 401 - return error for caller to handle redirect
      if (normalizedError.status === 401 && isBrowser()) {
        log('warn', '401 Unauthorized - returning error for caller to handle');
        // Clear invalid token
        setAuthToken(null);
        // Return normalized error - caller decides whether to redirect
        return Promise.reject(normalizedError);
      }

      // Show error toast for non-retryable errors
      // Note: Retry logic is handled at the useApi/usePolling hook level
      // We don't retry at axios level to avoid duplicate retries
      if (normalizedError.status !== 401) {
        message.error(normalizedError.message);
      }

      return Promise.reject(normalizedError);
    },
  );

  return instance;
};

export const apiClient = createApiClient();

export const setAuthToken = (token: string | null): void => {
  if (isBrowser()) {
    const storage = getLocalStorage();
    if (storage) {
      if (token) {
        storage.setItem('authToken', token);
      } else {
        storage.removeItem('authToken');
      }
    }
  }
  setDefaultHeaders(apiClient, token);
};

export const getAuthToken = (): string | null => {
  if (isBrowser()) {
    return getLocalStorage()?.getItem('authToken') ?? null;
  }
  return null;
};