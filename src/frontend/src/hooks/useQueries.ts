import { useQuery, useMutation, useQueryClient, type UseQueryOptions, type UseMutationOptions } from '@tanstack/react-query';
import {
  productApi,
  creatorApi,
  orderApi,
  healthApi,
  syncApi,
  dashboardApi,
  complianceApi,
  mediaApi,
  videoApi,
  accountApi,
  authApi,
  alertApi,
  alertDouyinApi,
  alertDianApi,
  type Product,
  type CreatorWork,
  type Order,
  type HealthResponse,
  type ExternalApiHealthResponse,
  type SyncHistoryItem,
  type DashboardStats,
  type ComplianceItem,
  type ComplianceStats,
  type ComplianceCheckResult,
  type ComplianceRule,
  type MediaItem,
  type Video,
  type Account,
  type AuthStatus,
  type AlertConfig,
  type AlertHistoryItem,
  type AlertStats,
  type PaginatedResponse,
} from '@/api';

// Query keys factory
export const queryKeys = {
  products: {
    all: ['products'] as const,
    lists: () => [...queryKeys.products.all, 'list'] as const,
    list: (params: Record<string, unknown>) => [...queryKeys.products.lists(), params] as const,
    stats: () => [...queryKeys.products.all, 'stats'] as const,
    detail: (id: string) => [...queryKeys.products.all, 'detail', id] as const,
  },
  creators: {
    all: ['creators'] as const,
    lists: () => [...queryKeys.creators.all, 'list'] as const,
    list: (params: Record<string, unknown>) => [...queryKeys.creators.lists(), params] as const,
    overview: (params: Record<string, unknown>) => [...queryKeys.creators.all, 'overview', params] as const,
    works: (params: Record<string, unknown>) => [...queryKeys.creators.all, 'works', params] as const,
    detail: (id: string) => [...queryKeys.creators.all, 'detail', id] as const,
  },
  orders: {
    all: ['orders'] as const,
    lists: () => [...queryKeys.orders.all, 'list'] as const,
    list: (params: Record<string, unknown>) => [...queryKeys.orders.lists(), params] as const,
    stats: () => [...queryKeys.orders.all, 'stats'] as const,
    detail: (id: string) => [...queryKeys.orders.all, 'detail', id] as const,
  },
  health: {
    all: ['health'] as const,
    check: () => [...queryKeys.health.all, 'check'] as const,
  },
  sync: {
    all: ['sync'] as const,
    history: (params: Record<string, unknown>) => [...queryKeys.sync.all, 'history', params] as const,
  },
  dashboard: {
    all: ['dashboard'] as const,
    stats: (params: Record<string, unknown>) => [...queryKeys.dashboard.all, 'stats', params] as const,
    mockStatus: () => [...queryKeys.dashboard.all, 'mock-status'] as const,
  },
  compliance: {
    all: ['compliance'] as const,
    lists: () => [...queryKeys.compliance.all, 'list'] as const,
    list: (params: Record<string, unknown>) => [...queryKeys.compliance.lists(), params] as const,
    stats: () => [...queryKeys.compliance.all, 'stats'] as const,
    rules: () => [...queryKeys.compliance.all, 'rules'] as const,
    ruleHistory: (id: string) => [...queryKeys.compliance.all, 'rule-history', id] as const,
  },
  media: {
    all: ['media'] as const,
    videoEdit: (params: Record<string, unknown>) => [...queryKeys.media.all, 'video-edit', params] as const,
    imageEdit: (params: Record<string, unknown>) => [...queryKeys.media.all, 'image-edit', params] as const,
  },
  videos: {
    all: ['videos'] as const,
    lists: () => [...queryKeys.videos.all, 'list'] as const,
    list: (params: Record<string, unknown>) => [...queryKeys.videos.lists(), params] as const,
    detail: (id: string) => [...queryKeys.videos.all, 'detail', id] as const,
  },
  accounts: {
    all: ['accounts'] as const,
    lists: () => [...queryKeys.accounts.all, 'list'] as const,
    list: (params: Record<string, unknown>) => [...queryKeys.accounts.lists(), params] as const,
    detail: (id: string) => [...queryKeys.accounts.all, 'detail', id] as const,
  },
  auth: {
    all: ['auth'] as const,
    status: () => [...queryKeys.auth.all, 'status'] as const,
    qrCode: () => [...queryKeys.auth.all, 'qr-code'] as const,
  },
  alerts: {
    all: ['alerts'] as const,
    config: () => [...queryKeys.alerts.all, 'config'] as const,
    douyinConfig: () => [...queryKeys.alerts.all, 'douyin-config'] as const,
    dianConfig: () => [...queryKeys.alerts.all, 'dian-config'] as const,
    history: (params: Record<string, unknown>) => [...queryKeys.alerts.all, 'history', params] as const,
    stats: () => [...queryKeys.alerts.all, 'stats'] as const,
  },
} as const;

// Helper to create query options with consistent defaults
function createQueryOptions<TData, TError>(
  queryKey: readonly unknown[],
  queryFn: () => Promise<TData>,
  options?: Partial<UseQueryOptions<TData, TError, TData, readonly unknown[]>>
): UseQueryOptions<TData, TError, TData, readonly unknown[]> {
  return {
    queryKey,
    queryFn,
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 30,
    retry: 2,
    ...options,
  };
}

// ==================== Products ====================

export function useProductsList(
  params: Record<string, unknown> = {},
  options?: Partial<UseQueryOptions<PaginatedResponse<Product>, Error, PaginatedResponse<Product>, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.products.list(params),
      () => productApi.getList(params) as Promise<PaginatedResponse<Product>>,
      options
    )
  );
}

export interface ProductStatsData {
  total: number;        // 总数
  onsale: number;       // 在售数
  stock: number;        // 库存预警数
  violation: number;    // 违规数
  [key: string]: unknown;
}

export function useProductsStats(
  options?: Partial<UseQueryOptions<ProductStatsData, Error, ProductStatsData, readonly unknown[]>>
): import('@tanstack/react-query').UseQueryResult<ProductStatsData, Error> {
  return useQuery(
    createQueryOptions<ProductStatsData, Error>(
      queryKeys.products.stats(),
      () => productApi.getStats() as Promise<ProductStatsData>,
      options
    )
  );
}

export function useProductDetail(
  id: string,
  options?: Partial<UseQueryOptions<Product, Error, Product, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.products.detail(id),
      () => productApi.getDetail(id) as Promise<Product>,
      { enabled: !!id, ...options }
    )
  );
}

// ==================== Creators ====================

export function useCreatorsList(
  params: Record<string, unknown> = {},
  options?: Partial<UseQueryOptions<PaginatedResponse<CreatorWork>, Error, PaginatedResponse<CreatorWork>, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.creators.list(params),
      () => creatorApi.getList(params) as Promise<PaginatedResponse<CreatorWork>>,
      options
    )
  );
}

export interface CreatorsOverviewData {
  total_followers?: number;
  today_new_followers?: number;
  avg_engagement_rate?: number;
  trend_data?: unknown[];
  data_source?: string;
  recent_days?: number;
  [key: string]: unknown;
}

export function useCreatorsOverview(
  params: Record<string, unknown> = {},
  options?: Partial<UseQueryOptions<CreatorsOverviewData, Error, CreatorsOverviewData, readonly unknown[]>>
): import('@tanstack/react-query').UseQueryResult<CreatorsOverviewData, Error> {
  return useQuery(
    createQueryOptions<CreatorsOverviewData, Error>(
      queryKeys.creators.overview(params),
      () => creatorApi.getOverview(params) as Promise<CreatorsOverviewData>,
      options
    )
  );
}

export function useCreatorsWorks(
  params: Record<string, unknown> = {},
  options?: Partial<UseQueryOptions<PaginatedResponse<CreatorWork>, Error, PaginatedResponse<CreatorWork>, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.creators.works(params),
      () => creatorApi.getWorks(params) as Promise<PaginatedResponse<CreatorWork>>,
      options
    )
  );
}

export function useCreatorDetail(
  id: string,
  options?: Partial<UseQueryOptions<CreatorWork, Error, CreatorWork, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.creators.detail(id),
      () => creatorApi.getDetail(id) as Promise<CreatorWork>,
      { enabled: !!id, ...options }
    )
  );
}

// ==================== Orders ====================

export function useOrdersList(
  params: Record<string, unknown> = {},
  options?: Partial<UseQueryOptions<PaginatedResponse<Order>, Error, PaginatedResponse<Order>, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.orders.list(params),
      () => orderApi.getList(params) as Promise<PaginatedResponse<Order>>,
      options
    )
  );
}

export interface OrderStatsData {
  all?: { count?: number; amount?: number };
  pay?: { count?: number; amount?: number };
  cancel?: { count?: number; amount?: number };
  sub_tab_count_map?: Record<string, { count?: number; amount?: number }>;
  [key: string]: unknown;
}

export function useOrdersStats(
  options?: Partial<UseQueryOptions<OrderStatsData, Error, OrderStatsData, readonly unknown[]>>
): import('@tanstack/react-query').UseQueryResult<OrderStatsData, Error> {
  return useQuery(
    createQueryOptions<OrderStatsData, Error>(
      queryKeys.orders.stats(),
      () => orderApi.getStats() as Promise<OrderStatsData>,
      options
    )
  );
}

// ==================== Health ====================

export function useHealthCheck(
  options?: Partial<UseQueryOptions<HealthResponse, Error, HealthResponse, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.health.check(),
      () => healthApi.check() as Promise<HealthResponse>,
      { refetchInterval: 1000 * 60 * 5, ...options }
    )
  );
}

export function useExternalApiHealth(
  options?: Partial<UseQueryOptions<ExternalApiHealthResponse, Error, ExternalApiHealthResponse, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      [...queryKeys.health.all, 'external'],
      () => healthApi.checkExternal() as Promise<ExternalApiHealthResponse>,
      { refetchInterval: 1000 * 60 * 5, ...options }
    )
  );
}

// ==================== Sync ====================

export function useSyncHistory(
  params: Record<string, unknown> = {},
  options?: Partial<UseQueryOptions<PaginatedResponse<SyncHistoryItem>, Error, PaginatedResponse<SyncHistoryItem>, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.sync.history(params),
      () => syncApi.getHistory(params) as Promise<PaginatedResponse<SyncHistoryItem>>,
      options
    )
  );
}

export function useManualSync(
  _options?: UseMutationOptions<{ success: boolean }, Error, boolean, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (asyncMode: boolean) => syncApi.manualSync(asyncMode) as Promise<{ success: boolean } | undefined>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.sync.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.health.all });
    },
  });
}

// ==================== Dashboard ====================

export function useDashboardStats(
  params: Record<string, unknown> = {},
  options?: Partial<UseQueryOptions<DashboardStats, Error, DashboardStats, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.dashboard.stats(params),
      () => dashboardApi.getStats(params) as Promise<DashboardStats>,
      { refetchInterval: 1000 * 60 * 2, ...options }
    )
  );
}

export function useDashboardMockStatus(
  options?: Partial<UseQueryOptions<Record<string, unknown>, Error, Record<string, unknown>, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.dashboard.mockStatus(),
      () => dashboardApi.getMockStatus() as Promise<Record<string, unknown>>,
      { refetchInterval: 1000 * 30, ...options }
    )
  );
}

// ==================== Compliance ====================

export function useComplianceList(
  params: Record<string, unknown> = {},
  options?: Partial<UseQueryOptions<PaginatedResponse<ComplianceItem>, Error, PaginatedResponse<ComplianceItem>, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.compliance.list(params),
      () => complianceApi.getList(params) as Promise<PaginatedResponse<ComplianceItem>>,
      options
    )
  );
}

export function useComplianceStats(
  options?: Partial<UseQueryOptions<ComplianceStats, Error, ComplianceStats, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.compliance.stats(),
      () => complianceApi.getStats() as Promise<ComplianceStats>,
      options
    )
  );
}

export function useComplianceRules(
  options?: Partial<UseQueryOptions<{ items: ComplianceRule[]; total: number }, Error, { items: ComplianceRule[]; total: number }, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.compliance.rules(),
      () => complianceApi.getRules() as Promise<{ items: ComplianceRule[]; total: number }>,
      options
    )
  );
}

export function useComplianceRuleHistory(
  id: string,
  options?: Partial<UseQueryOptions<{ items: ComplianceItem[]; total: number }, Error, { items: ComplianceItem[]; total: number }, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.compliance.ruleHistory(id),
      () => complianceApi.getRuleHistory(id) as Promise<{ items: ComplianceItem[]; total: number }>,
      { enabled: !!id, ...options }
    )
  );
}

export function useIgnoreCompliance(
  _options?: UseMutationOptions<ComplianceItem, Error, string, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => complianceApi.ignore(id) as Promise<ComplianceItem>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.stats() });
    },
  });
}

export function useTakeDownCompliance(
  _options?: UseMutationOptions<ComplianceItem, Error, string, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => complianceApi.takeDown(id) as Promise<ComplianceItem>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.stats() });
    },
  });
}

export function useRestoreCompliance(
  _options?: UseMutationOptions<ComplianceItem, Error, string, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => complianceApi.restore(id) as Promise<ComplianceItem>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.stats() });
    },
  });
}

export function useTriggerComplianceCheck(
  _options?: UseMutationOptions<ComplianceCheckResult, Error, void, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => complianceApi.triggerCheck() as Promise<ComplianceCheckResult>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.stats() });
    },
  });
}

export function useCheckProductsCompliance(
  _options?: UseMutationOptions<ComplianceCheckResult, Error, void, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => complianceApi.checkProducts() as Promise<ComplianceCheckResult>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.stats() });
    },
  });
}

export function useCheckWorksCompliance(
  _options?: UseMutationOptions<ComplianceCheckResult, Error, void, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => complianceApi.checkWorks() as Promise<ComplianceCheckResult>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.stats() });
    },
  });
}

export function useCreateComplianceRule(
  _options?: UseMutationOptions<ComplianceRule, Error, Partial<ComplianceRule>, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (rule: Partial<ComplianceRule>) => complianceApi.createRule(rule) as Promise<ComplianceRule>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.rules() });
    },
  });
}

export function useUpdateComplianceRule(
  _options?: UseMutationOptions<ComplianceRule, Error, { id: string; rule: Partial<ComplianceRule> }, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, rule }: { id: string; rule: Partial<ComplianceRule> }) => complianceApi.updateRule(id, rule) as Promise<ComplianceRule>,
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.rules() });
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.ruleHistory(id) });
    },
  });
}

export function useDeleteComplianceRule(
  _options?: UseMutationOptions<unknown, Error, string, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => complianceApi.deleteRule(id) as Promise<unknown>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.compliance.rules() });
    },
  });
}

// ==================== Media ====================

export function useVideoEditList(
  params: Record<string, unknown> = {},
  options?: Partial<UseQueryOptions<PaginatedResponse<MediaItem>, Error, PaginatedResponse<MediaItem>, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.media.videoEdit(params),
      () => mediaApi.getVideoEditList(params) as Promise<PaginatedResponse<MediaItem>>,
      options
    )
  );
}

export function useImageEditList(
  params: Record<string, unknown> = {},
  options?: Partial<UseQueryOptions<PaginatedResponse<MediaItem>, Error, PaginatedResponse<MediaItem>, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.media.imageEdit(params),
      () => mediaApi.getImageEditList(params) as Promise<PaginatedResponse<MediaItem>>,
      options
    )
  );
}

export function useCreateMedia(
  _options?: UseMutationOptions<MediaItem, Error, Partial<MediaItem>, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<MediaItem>) => mediaApi.create(data) as Promise<MediaItem>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.media.all });
    },
  });
}

export function useUpdateMedia(
  _options?: UseMutationOptions<MediaItem, Error, { id: string; data: Partial<MediaItem> }, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<MediaItem> }) => mediaApi.update(id, data) as Promise<MediaItem>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.media.all });
    },
  });
}

// ==================== Videos ====================

export function useVideosList(
  params: Record<string, unknown> = {},
  options?: Partial<UseQueryOptions<PaginatedResponse<Video>, Error, PaginatedResponse<Video>, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.videos.list(params),
      () => videoApi.getList(params) as Promise<PaginatedResponse<Video>>,
      options
    )
  );
}

export function useVideoDetail(
  id: string,
  options?: Partial<UseQueryOptions<Video, Error, Video, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.videos.detail(id),
      () => videoApi.getDetail(id) as Promise<Video>,
      { enabled: !!id, ...options }
    )
  );
}

export function useCreateVideo(
  _options?: UseMutationOptions<Video, Error, Partial<Video>, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Video>) => videoApi.create(data) as Promise<Video>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.videos.lists() });
    },
  });
}

export function useUpdateVideo(
  _options?: UseMutationOptions<Video, Error, { id: string; data: Partial<Video> }, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Video> }) => videoApi.update(id, data) as Promise<Video>,
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.videos.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.videos.detail(id) });
    },
  });
}

export function useDeleteVideo(
  _options?: UseMutationOptions<unknown, Error, string, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => videoApi.delete(id) as Promise<unknown>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.videos.lists() });
    },
  });
}

// ==================== Accounts ====================

export function useAccountsList(
  params: Record<string, unknown> = {},
  options?: Partial<UseQueryOptions<PaginatedResponse<Account>, Error, PaginatedResponse<Account>, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.accounts.list(params),
      () => accountApi.getList(params) as Promise<PaginatedResponse<Account>>,
      options
    )
  );
}

export function useAccountDetail(
  id: string,
  options?: Partial<UseQueryOptions<Account, Error, Account, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.accounts.detail(id),
      () => accountApi.getDetail(id) as Promise<Account>,
      { enabled: !!id, ...options }
    )
  );
}

export function useCreateAccount(
  _options?: UseMutationOptions<Account, Error, Partial<Account>, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Account>) => accountApi.create(data) as Promise<Account>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts.lists() });
    },
  });
}

export function useUpdateAccount(
  _options?: UseMutationOptions<Account, Error, { id: string; data: Partial<Account> }, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Account> }) => accountApi.update(id, data) as Promise<Account>,
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts.detail(id) });
    },
  });
}

export function useDeleteAccount(
  _options?: UseMutationOptions<unknown, Error, string, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => accountApi.delete(id) as Promise<unknown>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts.lists() });
    },
  });
}

// ==================== Auth ====================

export function useAuthStatus(
  options?: Partial<UseQueryOptions<AuthStatus, Error, AuthStatus, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.auth.status(),
      () => authApi.getStatus() as Promise<AuthStatus>,
      options
    )
  );
}

export function useAuthLogin(
  _options?: UseMutationOptions<{ auth_url: string }, Error, void, unknown>
) {
  return useMutation({
    mutationFn: () => authApi.login() as Promise<{ auth_url: string }>,
  });
}

export function useAuthLogout(
  _options?: UseMutationOptions<unknown, Error, void, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => authApi.logout() as Promise<unknown>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.all });
    },
  });
}

export function useAuthQrCode(
  _options?: UseMutationOptions<{ auth_url: string }, Error, void, unknown>
) {
  return useMutation({
    mutationFn: () => authApi.getQrCode() as Promise<{ auth_url: string }>,
  });
}

// ==================== Alerts ====================

export function useAlertConfig(
  options?: Partial<UseQueryOptions<AlertConfig, Error, AlertConfig, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.alerts.config(),
      () => alertApi.getConfig() as Promise<AlertConfig>,
      options
    )
  );
}

export function useAlertDouyinConfig(
  options?: Partial<UseQueryOptions<AlertConfig, Error, AlertConfig, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.alerts.douyinConfig(),
      () => alertDouyinApi.getConfig() as Promise<AlertConfig>,
      options
    )
  );
}

export function useAlertDianConfig(
  options?: Partial<UseQueryOptions<AlertConfig, Error, AlertConfig, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.alerts.dianConfig(),
      () => alertDianApi.getConfig() as Promise<AlertConfig>,
      options
    )
  );
}

export function useUpdateAlertConfig(
  _options?: UseMutationOptions<AlertConfig, Error, AlertConfig, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (config: AlertConfig) => alertApi.updateConfig(config) as Promise<AlertConfig>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts.config() });
    },
  });
}

export function useUpdateAlertDouyinConfig(
  _options?: UseMutationOptions<AlertConfig, Error, AlertConfig, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (alertConfig: AlertConfig) => alertDouyinApi.updateConfig(alertConfig) as Promise<AlertConfig>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts.douyinConfig() });
    },
  });
}

export function useUpdateAlertDianConfig(
  _options?: UseMutationOptions<AlertConfig, Error, AlertConfig, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (alertConfig: AlertConfig) => alertDianApi.updateConfig(alertConfig) as Promise<AlertConfig>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts.dianConfig() });
    },
  });
}

export function useAlertHistory(
  params: Record<string, unknown> = {},
  options?: Partial<UseQueryOptions<PaginatedResponse<AlertHistoryItem>, Error, PaginatedResponse<AlertHistoryItem>, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.alerts.history(params),
      () => alertApi.getHistory(params) as Promise<PaginatedResponse<AlertHistoryItem>>,
      options
    )
  );
}

export function useAlertStats(
  options?: Partial<UseQueryOptions<AlertStats, Error, AlertStats, readonly unknown[]>>
) {
  return useQuery(
    createQueryOptions(
      queryKeys.alerts.stats(),
      () => alertApi.getStats() as Promise<AlertStats>,
      options
    )
  );
}

export function useClearAlertHistory(
  _options?: UseMutationOptions<{ cleared: number }, Error, void, unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => alertApi.clearHistory() as Promise<{ cleared: number }>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts.history({}) });
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts.stats() });
    },
  });
}