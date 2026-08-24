import axios from 'axios';
// Use any for axios internal types since they're not exported in v1.6+
interface AxiosError<T = unknown> {
  isAxiosError: boolean;
  message: string;
  response?: { data: T; status: number };
}
type AxiosRequestConfig = any;
interface AxiosResponse<T = unknown> {
  data: T;
  status: number;
  config: any;
}
type AxiosXHR<T = unknown> = any;
type InternalAxiosRequestConfig = any;
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

const isRetryableError = (error: NormalizedError): boolean => {
  return error.retryable || error.code === 'NETWORK_ERROR' || (typeof error.status === 'number' && error.status >= 500);
};

const normalizeError = (error: unknown): NormalizedError => {
  const timestamp = new Date().toISOString();

  if (error && typeof error === 'object' && 'isAxiosError' in error && (error as { isAxiosError: boolean }).isAxiosError) {
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
    const data = axiosError.response.data as { message?: string; code?: string; details?: unknown } | undefined;

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

const createApiClient = () => {
  // Ensure baseURL includes /api/v1 prefix
  const baseURL = config.apiBaseUrl ? `${config.apiBaseUrl}/api/v1` : '/api/v1';
  
  const instance = axios.create({
    baseURL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  instance.interceptors.request.use(
    (requestConfig: InternalAxiosRequestConfig) => {
      // Priority: localStorage token > VITE_API_KEY env var
      const authToken = isBrowser() ? getLocalStorage()?.getItem('authToken') : null;
      const apiKey = import.meta.env.VITE_API_KEY;
      const token = authToken || (apiKey && apiKey !== 'your_api_key_here' ? apiKey : null);
      
      if (token && requestConfig.headers) {
        requestConfig.headers.Authorization = `Bearer ${token}`;
      }

      log('debug', `API Request: ${requestConfig.method?.toUpperCase()} ${requestConfig.url}`);
      return requestConfig;
    },
    (error) => {
      log('error', 'API Request Error:', error);
      return Promise.reject(normalizeError(error));
    }
  );

  instance.interceptors.response.use(
    (response: AxiosXHR<unknown>) => {
      log('debug', `API Response: ${response.status} ${response.config.url}`);
      return response;
    },
    async (error) => {
      const normalizedError = normalizeError(error);
      log('error', `API Error: ${normalizedError.code} - ${normalizedError.message}`, normalizedError);

      const originalRequest = error.config as AxiosRequestConfig & { _retryCount?: number };
      const maxRetries = 2;
      const currentRetry = originalRequest._retryCount ?? 0;

      // Handle 401 - return error for caller to handle redirect
      if (normalizedError.status === 401 && isBrowser()) {
        log('warn', '401 Unauthorized - returning error for caller to handle');
        // Clear invalid token
        setAuthToken(null);
        // Return normalized error - caller decides whether to redirect
        return Promise.reject(normalizedError);
      }

      // Show error toast for non-retryable errors (avoid spamming during retries)
      const willRetry = isRetryableError(normalizedError) && currentRetry < maxRetries && originalRequest.method !== 'POST';
      if (!willRetry && normalizedError.status !== 401) {
        message.error(normalizedError.message);
      }

      if (willRetry) {
        originalRequest._retryCount = currentRetry + 1;
        const delay = Math.min(1000 * 2 ** currentRetry, 10000);
        log('info', `Retrying request (${currentRetry + 1}/${maxRetries}) after ${delay}ms`);

        await new Promise((resolve) => setTimeout(resolve, delay));
        return instance(originalRequest);
      }

      return Promise.reject(normalizedError);
    }
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
};

export const getAuthToken = (): string | null => {
  if (isBrowser()) {
    return getLocalStorage()?.getItem('authToken') ?? null;
  }
  return null;
}