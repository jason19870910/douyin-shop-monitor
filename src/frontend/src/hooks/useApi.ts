import { useQuery, type UseQueryOptions, type QueryKey } from '@tanstack/react-query';

export function useApi<TData, TError = Error>(
  queryFn: () => Promise<TData>,
  queryKey: QueryKey,
  options?: Partial<UseQueryOptions<TData, TError, TData, QueryKey>>
) {
  return useQuery({
    queryKey,
    queryFn,
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 30,
    retry: 2,
    ...options,
  });
}