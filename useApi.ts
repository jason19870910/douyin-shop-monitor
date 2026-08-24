import { useState, useEffect, useCallback, useRef, type DependencyList } from 'react';
import { NormalizedError } from '@/api/index';

export type ApiStatus = 'idle' | 'loading' | 'success' | 'error';

export interface UseApiState<T> {
  data: T | null;
  status: ApiStatus;
  error: NormalizedError | null;
  retryCount: number;
}

export interface UseApiReturn<T> extends UseApiState<T> {
  refetch: () => Promise<T>;
  clearError: () => void;
  /** @deprecated Use `status === 'loading'` instead */
  loading: boolean;
}

type Thenable<T> = PromiseLike<T> | T;

const MAX_RETRIES = 2;
const RETRY_DELAY_BASE = 1000;

// eslint-disable-next-line react-hooks/set-state-in-effect
export function useApi<T>(
  apiCall: () => Thenable<T>,
  dependencies: DependencyList = [],
  options: { maxRetries?: number; retryOnError?: boolean } = {}
): UseApiReturn<T> {
  const { maxRetries = MAX_RETRIES, retryOnError = false } = options;

  const [data, setData] = useState<T | null>(null);
  const [status, setStatus] = useState<ApiStatus>('idle');
  const [error, setError] = useState<NormalizedError | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const isMountedRef = useRef(true);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      abortControllerRef.current?.abort();
    };
  }, []);

  const fetchData = useCallback(async (): Promise<T> => {
    if (!isMountedRef.current) return Promise.reject(new Error('Component unmounted'));

    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();

    setStatus('loading');
    setError(null);

    let attempt = 0;
    const maxAttempts = retryOnError ? maxRetries + 1 : 1;

    while (attempt < maxAttempts) {
      try {
        if (!isMountedRef.current) return Promise.reject(new Error('Component unmounted'));

        const result = await apiCall();
        if (!isMountedRef.current) return Promise.reject(new Error('Component unmounted'));

        setData(result);
        setStatus('success');
        setError(null);
        setRetryCount(0);
        return result;
      } catch (err) {
        if (!isMountedRef.current) return Promise.reject(new Error('Component unmounted'));

        const normalizedError = err as NormalizedError;
        const isRetryable = normalizedError.retryable === true;

        if (isRetryable && attempt < maxRetries && retryOnError) {
          attempt++;
          setRetryCount(attempt);
          const delay = RETRY_DELAY_BASE * 2 ** (attempt - 1);
          await new Promise((resolve) => setTimeout(resolve, delay));
          continue;
        }

        // Non-retryable or max retries reached
        setStatus('error');
        setError(normalizedError);
        setRetryCount(0);
        throw normalizedError;
      }
    }

    // Should not reach here
    throw new Error('Unexpected retry loop exit');
  }, [apiCall, maxRetries, retryOnError]);

  const clearError = useCallback(() => {
    setError(null);
    if (status === 'error') {
      setStatus('idle');
    }
  }, [status]);

  useEffect(() => {
    let cancelled = false;

    const execute = async () => {
      try {
        await fetchData();
      } catch {
        // Error is handled in fetchData
      }
    };

    if (!cancelled) {
      execute();
    }

    return () => {
      cancelled = true;
    };
  }, [...dependencies, fetchData]);

  return { data, status, error, retryCount, refetch: fetchData, clearError, loading: status === 'loading' };
}

export function usePolling<T>(
  apiCall: () => Thenable<T>,
  interval = 30000,
  options: { maxRetries?: number; retryOnError?: boolean } = {}
): UseApiReturn<T> {
  const { data, status, error, retryCount, refetch, clearError } = useApi(apiCall, [], options);

  const intervalRef = useRef<number | null>(null);
  const statusRef = useRef(status);

  // Update ref in useEffect to avoid "Cannot update ref during render" error
  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  useEffect(() => {
    const tick = () => {
      if (statusRef.current !== 'loading') {
        refetch().catch(() => {
          // Error handled in refetch
        });
      }
    };

    intervalRef.current = window.setInterval(tick, interval);

    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [interval, refetch]);

  return { data, status, error, retryCount, refetch, clearError, loading: status === 'loading' };
}

export type { NormalizedError };