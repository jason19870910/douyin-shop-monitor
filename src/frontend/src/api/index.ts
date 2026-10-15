import { apiClient } from '@/utils/apiClient';

// Re-export types from apiClient
export type { NormalizedError } from '@/utils/apiClient';

// 通用响应格式 - 前后端统一返回结构
export interface ApiResponse<T = unknown> {
  success?: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// 分页响应格式 - 用于 /api/products, /api/creators 等返回的结构
// 后端返回: { data: { items: T[], total: number, page?: number, size?: number }, success, message, error }
// 前端使用时通过 .data 获取 { items, total, page, size }
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page?: number;
  size?: number;
}

// 订单
export interface Order {
  order_id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  amount: number;
  status: string;
  create_time: string;
  pay_time?: string;
  [key: string]: unknown;
}

// 账户
export interface Account {
  account_id: string;
  account_name: string;
  account_type: string;
  phone: string;
  email: string;
  status: string;
  last_login: string | null;
  create_time: string;
  [key: string]: unknown;
}

// 创作者统计数据接口
export interface CreatorOverviewData {
  // 基础概览字段
  total_followers: number;        // 总粉丝数
  total_videos: number;           // 近期投稿量（7天）
  recent_view: number;            // 近期播放量（7天）
  recent_like: number;            // 近期点赞数（7天）
  
  // 互动详情（7天聚合）
  recent_share: number;           // 近期分享数
  recent_comment: number;         // 近期评论数
  recent_homepage_view: number;   // 近期主页访问
  
  // 粉丝变化（7天聚合）
  net_followers_gain: number;     // 净增粉丝
  cancel_followers: number;       // 取关粉丝
  
  // 视频质量指标（7天聚合）
  completion_rate_5s: number;     // 5秒完播率
  bounce_rate_2s: number;         // 2秒跳出率
  avg_view_second: number;        // 平均播放时长(秒)
  cover_click_ratio: number;      // 封面点击率
  
  // 兼容字段（实际为近期7天数据）
  total_views: number;            // 兼容：近期总播放
  total_likes: number;            // 兼容：近期总点赞
  total_comments: number;         // 兼容：近期总评论
  total_shares: number;           // 兼容：近期总分享
  
  // 元数据
  data_source?: string;           // 数据来源
  recent_days?: number;           // 统计天数
}

// 创作者作品
export interface CreatorWork {
  work_id: string;
  title?: string;
  name?: string;
  creator_name?: string;
  creator_id: string;
  cover_url?: string;
  cover?: string;
  play_count?: number;
  like_count?: number;
  comment_count?: number;
  share_count?: number;
  status?: number;
  create_time?: string;
  update_time?: string;
  duration?: number;
  video_url?: string;
  fetched_at?: string;
  [key: string]: unknown;
}

// 视频
export interface Video {
  video_id: string;
  title: string;
  creator_name: string;
  play_count: number;
  like_count: number;
  comment_count: number;
  share_count: number;
  status: string;
  create_time: string;
  [key: string]: unknown;
}

// 合规检查记录（对应后端 /api/v1/compliance 实际返回的 log 结构）
export interface ComplianceItem {
  id: string;
  status: 'pass' | 'fail' | 'warning' | 'ignored' | 'taken_down' | 'restored';
  target_type?: 'work' | 'product' | 'all';
  productId?: string;           // ⭐ 新增：产品ID（商品合规专用）
  product_title?: string;       // ⭐ 新增：产品标题（商品合规专用）
  rule_id?: string;
  ignored_at?: string;
  ignored_by?: string;
  taken_down_at?: string;
  taken_down_by?: string;
  restored_at?: string;
  restored_by?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

// 合规规则（对应后端 /api/v1/compliance/rules 存储结构）
export interface ComplianceRule {
  id: string;
  rule_name: string;
  rule_type: 'KEYWORD' | 'REGEX' | 'PRICE' | 'LICENSE' | 'ML_MODEL' | 'CUSTOM_SCRIPT' | 'HAOHUO_IMAGE' | 'HAOHUO_SPEC' | 'HAOHUO_PRICE' | 'HAOHUO_FATAL';
  rule_content: Record<string, unknown>;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  category: string;
  enabled: boolean;
  applicable_to?: ('product' | 'work')[];
  created_at: string;
  updated_at: string;
  [key: string]: unknown;
}

// 合规规则变更历史（规则操作日志）
export interface ComplianceLog {
  id: string;
  rule_id: string;
  action: 'create' | 'update' | 'delete' | 'enable' | 'disable';
  operator: string;
  created_at: string;
  [key: string]: unknown;
}

// 合规统计（对应后端 /api/v1/compliance/stats 实际返回结构）
export interface ComplianceStats {
  total_checks: number;
  passed: number;
  failed: number;
  warning: number;
  ignored: number;
  taken_down: number;
  by_category: Record<string, number>;
  by_rule: Record<string, number>;
}

// 合规检查结果（后端 fetch_and_check_compliance 当前为占位实现）
export interface ComplianceCheckResult {
  status: string;
  message?: string;
}

// 媒体项
export interface MediaItem {
  media_id: string;
  type: 'video' | 'image';
  title: string;
  status: string;
  source_url: string;
  output_url: string;
  create_time: string;
  [key: string]: unknown;
}

// 告警配置
export interface AlertConfig {
  sales_drop_threshold?: number;
  conversion_drop_threshold?: number;
  inventory_low_threshold?: number;
  notification_email?: string;
  enabled?: boolean;
  video_view_drop_threshold?: number;
  video_like_drop_threshold?: number;
  creator_follower_drop_threshold?: number;
  product_sales_drop_threshold?: number;
  order_refund_rate_threshold?: number;
  compliance_risk_threshold?: string;
}

// 告警历史
export interface AlertHistoryItem {
  type: string;
  product_id: string;
  product_name: string;
  message: string;
  drop_rate?: number;
  inventory?: number;
  threshold?: number;
  timestamp: string;
}

// 告警统计接口
export interface AlertStats {
  total: number;
  by_type: Record<string, number>;
}

// 同步历史
export interface SyncHistoryItem {
  timestamp: string;
  duration_ms: number;
  status: 'success' | 'failed';
  trigger: 'scheduled' | 'manual';
  details?: Record<string, string>;
  error?: string;
}

// 认证状态
export interface AuthStatus {
  douyin_app_id: string;
  douyin_app_secret: string;
  redirect_uri: string;
  authorized: boolean;
  access_token: string;
  refresh_token: string;
  expires_at: number;
  scope: string[];
}

// 仪表盘统计
export interface DashboardStats {
  total_sales_today: number;
  total_sales_yesterday: number;
  total_revenue_today: number;
  total_revenue_yesterday: number;
  total_orders_today: number;
  total_orders_yesterday: number;
  avg_conversion_rate: number;
  avg_conversion_rate_yesterday: number;
  sales_trend: Array<{ date: string; sales: number }> | string;
  revenue_trend: Array<{ date: string; sales: number }>;
  order_trend: Array<{ date: string; sales: number }>;
  top_products: Product[];
  data_source?: 'real' | 'mock' | 'cache';
  products?: { total: number; on_sale?: number; avg_conversion_rate_yesterday?: number };
  orders?: { total: number; total_amount?: number };
  creators?: { total: number; total_followers?: number };
  videos?: { total: number; total_views?: number };
  order_status_distribution?: Record<string, { count: number; amount: number }>;
  recent_orders?: Order[];
  timestamp?: string;
}

// 商品（用于DashboardStats.top_products）
export interface Product {
  product_id: string;
  product_name: string;
  category?: string;
  price: number;
  market_price?: number;
  discount_price?: number;
  sales_today: number;
  sales_yesterday: number;
  inventory: number;
  conversion_rate: number;
  status?: string;
  product_url?: string;
  img?: string;
  fetched_at?: string;
  [key: string]: unknown;
}

// Mock状态
export interface MockStatusItem {
  is_mock: boolean;
  elapsed_minutes: number;
  alert_threshold: number;
  alert_triggered: boolean;
  alert_sent: boolean;
}

export interface MockStatus {
  products: MockStatusItem;
  orders: MockStatusItem;
  creators: MockStatusItem;
}

// 健康检查响应
export interface HealthResponse {
  status: string;
  last_update: string;
  timestamp: string;
}

// 外部API健康检查响应
export interface ExternalApiHealthEndpoint {
  name: string;
  url: string;
  status: 'healthy' | 'unhealthy' | 'timeout' | 'connection_error' | 'error';
  status_code: number | null;
  response_time_ms: number | null;
  error: string | null;
}

export interface ExternalApiHealthResponse {
  overall_status: 'healthy' | 'degraded' | 'unhealthy';
  healthy_count: number;
  total_count: number;
  endpoints: ExternalApiHealthEndpoint[];
  timestamp: string;
}

/** Wrapper used by dashboardApi.getStats */
export type DashboardStatsResponse = ApiResponse<DashboardStats> | DashboardStats;

/** Wrapper used by other APIs that return direct data */
export type CreatorOverviewResponse = ApiResponse<CreatorOverviewData>;

// Mock状态响应类型
export type MockStatusResponse = ApiResponse<MockStatus> | MockStatus;

// 产品API
export interface ProductListParams {
  start_date?: string;  // YYYY-MM-DD
  end_date?: string;    // YYYY-MM-DD
  [key: string]: unknown;
}

export const productApi = {
  getList: (params?: ProductListParams) =>
    apiClient.get<ApiResponse<PaginatedResponse<Product>>>('/products', { params }).then((res) => res.data?.data),
  getExternal: (params?: ProductListParams) =>
    apiClient.get<ApiResponse<PaginatedResponse<Product>>>('/products/external', { params }).then((res) => res.data?.data),
  getStats: (params?: Record<string, unknown>) =>
    apiClient.get<ApiResponse<Record<string, unknown>>>('/products/stats', { params }).then((res) => res.data?.data),
  getDetail: (id: string) =>
    apiClient.get<ApiResponse<Product>>(`/products/${id}`).then((res) => res.data?.data),
  create: (data: Partial<Product>) =>
    apiClient.post<ApiResponse<Product>>('/products', data).then((res) => res.data?.data),
  update: (id: string, data: Partial<Product>) =>
    apiClient.put<ApiResponse<Product>>(`/products/${id}`, data).then((res) => res.data?.data),
  delete: (id: string) =>
    apiClient.delete<ApiResponse<unknown>>(`/products/${id}`).then((res) => res.data?.data),
};

// 创作者API
export const creatorApi = {
  getList: (params?: Record<string, unknown>) =>
    apiClient.get<ApiResponse<PaginatedResponse<CreatorWork>>>('/creators', { params }).then((res) => res.data?.data),
  getOverview: (params?: Record<string, unknown>) =>
    apiClient.get<ApiResponse<CreatorOverviewData>>('/creators/overview', { params }).then((res) => res.data?.data),
  getExternalWorks: (params?: Record<string, unknown>) =>
    apiClient.get<ApiResponse<PaginatedResponse<CreatorWork>>>('/creators/works/external', { params }).then((res) => res.data?.data),
  getWorks: (params?: Record<string, unknown>) =>
    apiClient.get<ApiResponse<PaginatedResponse<CreatorWork>>>('/creators/works', { params }).then((res) => res.data?.data),
  getDetail: (id: string) =>
    apiClient.get<ApiResponse<CreatorWork>>(`/creators/${id}`).then((res) => res.data?.data),
  create: (data: Partial<CreatorWork>) =>
    apiClient.post<ApiResponse<CreatorWork>>('/creators', data).then((res) => res.data?.data),
  update: (id: string, data: Partial<CreatorWork>) =>
    apiClient.put<ApiResponse<CreatorWork>>(`/creators/${id}`, data).then((res) => res.data?.data),
  delete: (id: string) =>
    apiClient.delete<ApiResponse<unknown>>(`/creators/${id}`).then((res) => res.data?.data),
};

// 订单API
export const orderApi = {
  getList: (params?: Record<string, unknown>) =>
    apiClient.get<ApiResponse<PaginatedResponse<Order>>>('/orders', { params }).then((res) => res.data?.data),
  getStats: () =>
    apiClient.get<ApiResponse<Record<string, unknown>>>('/orders/stats').then((res) => res.data?.data),
  getDetail: (id: string) =>
    apiClient.get<ApiResponse<Order>>(`/orders/${id}`).then((res) => res.data?.data),
  create: (data: Partial<Order>) =>
    apiClient.post<ApiResponse<Order>>('/orders', data).then((res) => res.data?.data),
  update: (id: string, data: Partial<Order>) =>
    apiClient.put<ApiResponse<Order>>(`/orders/${id}`, data).then((res) => res.data?.data),
  delete: (id: string) =>
    apiClient.delete<ApiResponse<unknown>>(`/orders/${id}`).then((res) => res.data?.data),
};

// 健康检查API
export const healthApi = {
  check: () => apiClient.get<ApiResponse<HealthResponse>>('/health').then((res) => res.data?.data),
  getHealth: () => apiClient.get<ApiResponse<HealthResponse>>('/health').then((res) => res.data?.data),
  checkExternal: () => apiClient.get<ApiResponse<ExternalApiHealthResponse>>('/health/external').then((res) => res.data?.data),
};

// 同步API
export const syncApi = {
  manualSync: (asyncMode = false) => apiClient.post<ApiResponse<{ success: boolean }>>('/sync/manual', { params: { async: asyncMode } }).then((res) => res.data?.data),
  getHistory: (params?: Record<string, unknown>) =>
    apiClient.get<ApiResponse<PaginatedResponse<SyncHistoryItem>>>('/sync/history', { params }).then((res) => res.data?.data),
};

// Dashboard API
export const dashboardApi = {
  getStats: (params?: Record<string, unknown>) =>
    apiClient.get<ApiResponse<DashboardStats>>('/dashboard/stats', { params }).then((res) => res.data?.data),
  getMockStatus: () => apiClient.get<ApiResponse<MockStatus>>('/mock/status').then((res) => res.data?.data),
};

// 合规API
export const complianceApi = {
  getList: (params?: Record<string, unknown>) =>
    apiClient.get<ApiResponse<PaginatedResponse<ComplianceItem>>>('/compliance', { params }).then((res) => res.data?.data),
  ignore: (id: string) =>
    apiClient.post<ApiResponse<ComplianceItem>>(`/compliance/${id}/ignore`).then((res) => res.data?.data),
  takeDown: (id: string) =>
    apiClient.post<ApiResponse<ComplianceItem>>(`/compliance/${id}/take-down`).then((res) => res.data?.data),
  restore: (id: string) =>
    apiClient.post<ApiResponse<ComplianceItem>>(`/compliance/${id}/restore`).then((res) => res.data?.data),
  getStats: () =>
    apiClient.get<ApiResponse<ComplianceStats>>('/compliance/stats').then((res) => res.data?.data),
  triggerCheck: () =>
    apiClient.post<ApiResponse<ComplianceCheckResult>>('/compliance/check').then((res) => res.data?.data),
  checkProducts: () =>
    apiClient.post<ApiResponse<ComplianceCheckResult>>('/compliance/check/products').then((res) => res.data?.data),
  checkWorks: () =>
    apiClient.post<ApiResponse<ComplianceCheckResult>>('/compliance/check/works').then((res) => res.data?.data),
  export: (params?: Record<string, unknown>) =>
    apiClient.get('/compliance/export', { params, responseType: 'blob' }).then((res) => res.data),
  getRules: () =>
    apiClient.get<ApiResponse<{ items: ComplianceRule[]; total: number }>>('/compliance/rules').then((res) => res.data?.data),
  createRule: (rule: Partial<ComplianceRule>) =>
    apiClient.post<ApiResponse<ComplianceRule>>('/compliance/rules', rule).then((res) => res.data?.data),
  updateRule: (id: string, rule: Partial<ComplianceRule>) =>
    apiClient.put<ApiResponse<ComplianceRule>>(`/compliance/rules/${id}`, rule).then((res) => res.data?.data),
  deleteRule: (id: string) =>
    apiClient.delete<ApiResponse<unknown>>(`/compliance/rules/${id}`).then((res) => res.data?.data),
  getRuleHistory: (id: string) =>
    apiClient.get<ApiResponse<{ items: ComplianceItem[]; total: number }>>(`/compliance/rules/${id}/history`).then((res) => res.data?.data),
  refresh: () =>
    apiClient.post<ApiResponse<{ refreshed: boolean }>>('/compliance/refresh').then((res) => res.data?.data),
};

// 媒体API
export const mediaApi = {
  getVideoEditList: (params?: Record<string, unknown>) =>
    apiClient.get<ApiResponse<PaginatedResponse<MediaItem>>>('/media/video-edit', { params }).then((res) => res.data?.data),
  getImageEditList: (params?: Record<string, unknown>) =>
    apiClient.get<ApiResponse<PaginatedResponse<MediaItem>>>('/media/image-edit', { params }).then((res) => res.data?.data),
  create: (data: Partial<MediaItem>) =>
    apiClient.post<ApiResponse<MediaItem>>('/media', data).then((res) => res.data?.data),
  update: (id: string, data: Partial<MediaItem>) =>
    apiClient.put<ApiResponse<MediaItem>>(`/media/${id}`, data).then((res) => res.data?.data),
  delete: (id: string) =>
    apiClient.delete<ApiResponse<unknown>>(`/media/${id}`).then((res) => res.data?.data),
};

// 告警API
export const alertDouyinApi = {
  getConfig: () => apiClient.get<ApiResponse<AlertConfig>>('/alerts/douyin/config').then((res) => res.data?.data),
  updateConfig: (alertConfig: AlertConfig) =>
    apiClient.post<ApiResponse<AlertConfig>>('/alerts/douyin/config', alertConfig).then((res) => res.data?.data),
};

export const alertDianApi = {
  getConfig: () => apiClient.get<ApiResponse<AlertConfig>>('/alerts/dian/config').then((res) => res.data?.data),
  updateConfig: (alertConfig: AlertConfig) =>
    apiClient.post<ApiResponse<AlertConfig>>('/alerts/dian/config', alertConfig).then((res) => res.data?.data),
};

// 视频API
export const videoApi = {
  getList: (params?: Record<string, unknown>) =>
    apiClient.get<ApiResponse<PaginatedResponse<Video>>>('/videos', { params }).then((res) => res.data?.data),
  getDetail: (id: string) =>
    apiClient.get<ApiResponse<Video>>(`/videos/${id}`).then((res) => res.data?.data),
  create: (data: Partial<Video>) =>
    apiClient.post<ApiResponse<Video>>('/videos', data).then((res) => res.data?.data),
  update: (id: string, data: Partial<Video>) =>
    apiClient.put<ApiResponse<Video>>(`/videos/${id}`, data).then((res) => res.data?.data),
  delete: (id: string) =>
    apiClient.delete<ApiResponse<unknown>>(`/videos/${id}`).then((res) => res.data?.data),
};

// 账户API
export const accountApi = {
  getList: (params?: Record<string, unknown>) =>
    apiClient.get<ApiResponse<PaginatedResponse<Account>>>('/accounts', { params }).then((res) => res.data?.data),
  getDetail: (id: string) =>
    apiClient.get<ApiResponse<Account>>(`/accounts/${id}`).then((res) => res.data?.data),
  create: (data: Partial<Account>) =>
    apiClient.post<ApiResponse<Account>>('/accounts', data).then((res) => res.data?.data),
  update: (id: string, data: Partial<Account>) =>
    apiClient.put<ApiResponse<Account>>(`/accounts/${id}`, data).then((res) => res.data?.data),
  delete: (id: string) =>
    apiClient.delete<ApiResponse<unknown>>(`/accounts/${id}`).then((res) => res.data?.data),
};

// 认证API
export const authApi = {
  getStatus: () =>
    apiClient.get<ApiResponse<AuthStatus>>('/auth/status').then((res) => res.data?.data),
  login: () =>
    apiClient.get<ApiResponse<{ auth_url: string }>>('/auth/login').then((res) => res.data?.data),
  logout: () =>
    apiClient.post<ApiResponse<unknown>>('/auth/logout').then((res) => res.data?.data),
  getQrCode: () =>
    apiClient.get<ApiResponse<{ auth_url: string }>>('/auth/qr-code').then((res) => res.data?.data),
};

// 用户资料接口
export interface UserProfile {
  user_id: string;
  username: string;
  email: string;
  phone: string;
  role: string;
  create_time: string;
  last_login: string;
  open_id: string;
  authorized: boolean;
  scope: string[];
  expires_in: number;
  is_expired: boolean;
  [key: string]: unknown;
}

// 用户资料API
export const profileApi = {
  getProfile: () =>
    apiClient.get<ApiResponse<UserProfile>>('/auth/profile').then((res) => res.data?.data),
  updateProfile: (data: Partial<Pick<UserProfile, 'email' | 'phone'>>) =>
    apiClient.put<ApiResponse<UserProfile>>('/auth/profile', data).then((res) => res.data?.data),
};

// ==================== 版本控制（内部系统信息） ====================

// 版本信息（/api/v1/version）
export interface VersionInfo {
  version: string;
  commit: string;
  builtAt: string;
  apiKeyInlined: boolean;
  environment: 'development' | 'production';
}

// 变更记录（/api/v1/changes）
export interface ChangeRecord {
  id: string;
  message: string;
  author: string;
  date: string;
  type: 'feat' | 'fix' | 'docs' | 'refactor' | 'chore' | 'test';
}

// 部署状态（/api/v1/status）
export interface DeploymentStatus {
  appHealthy: boolean;
  redisHealthy: boolean;
  frontendHealthy: boolean;
  lastDeploy: string | null;
}

// 环境配置（/api/v1/env）
export interface EnvConfig {
  VITE_API_KEY: string | null;
  VITE_DEV_MODE: boolean | null;
  VITE_ENABLE_MOCK_FALLBACK: boolean | null;
}

// 版本控制API
export const versionApi = {
  getVersion: () =>
    apiClient.get<ApiResponse<VersionInfo>>('/version').then((res) => res.data?.data),
  getChanges: () =>
    apiClient.get<ApiResponse<ChangeRecord[]>>('/changes').then((res) => res.data?.data),
  getStatus: () =>
    apiClient.get<ApiResponse<DeploymentStatus>>('/status').then((res) => res.data?.data),
  getEnv: () =>
    apiClient.get<ApiResponse<EnvConfig>>('/env').then((res) => res.data?.data),
};

// ==================== 创作者收益（外部抖音数据） ====================

// Creator 收益概览（/api/v1/external/creator/income/summary）
export interface CreatorIncomeCategory {
  category_id?: string;
  name: string;
  amount?: number;
  yesterday_total_income?: number;
  today_total_income?: number;
  icon?: string;
  light_color_icon?: string;
  link_relative?: number;
  data_update_desc?: string;
  data_update_status?: number;
  has_link_relative?: boolean;
  has_today_total_income?: boolean;
}
export interface CreatorIncomePeriodSummary {
  category_list: CreatorIncomeCategory[];
  history_total_income?: number;
  data_update_status?: number;
  fail_reason?: string;
  has_link_relative?: boolean;
}
export interface CreatorIncomeTotalSummary {
  category_list: CreatorIncomeCategory[];
  data_update_status?: number;
  fail_reason?: string | null;
  has_link_relative?: boolean;
  history_total_income?: number;
  link_relative?: number;
}
export interface CreatorIncomeSummary {
  status_code: number;
  status_msg?: string;
  today_total_income: number;
  total_balance: number;
  has_today_total_income?: boolean;
  day1_income_summary: CreatorIncomePeriodSummary;
  day7_income_summary: CreatorIncomePeriodSummary;
  day30_income_summary: CreatorIncomePeriodSummary;
  total_income_summary: CreatorIncomeTotalSummary;
  extra?: { now: number };
  data_update_status?: number;
  fail_reason?: string | null;
  link_relative?: number;
}

// Creator 收益趋势（/api/v1/external/creator/income/detail）
export interface IncomeItem {
  amount: number;
  name: string;
  timestamp: number;
}
export interface ChartCoordinate {
  x: number;
  y: number;
}
export interface CreatorIncomeDetail {
  status_code: number;
  status_msg?: string;
  fail_reason?: string | null;
  chart_coordinate_list: ChartCoordinate[];
  income_item_list: IncomeItem[];
  media_item_list?: unknown | null;
  extra?: { now: number };
}

// 创作者收益API
export const earningsApi = {
  getIncomeSummary: () =>
    apiClient.get<ApiResponse<CreatorIncomeSummary>>('/external/creator/income/summary').then((res) => res.data?.data),
  getIncomeDetail: () =>
    apiClient.get<ApiResponse<CreatorIncomeDetail>>('/external/creator/income/detail').then((res) => res.data?.data),
};

// ==================== 抖店 Compass 经营概况 ====================

// Compass 经营概况（/api/v1/external/compass/shop/core-index）
export interface CompassIndexValue {
  value?: string | number;
  unit?: string;
}
export interface CompassIndexItem {
  index_name: string;
}
export interface CompassCardValue {
  basic_meta: CompassIndexItem[];
  data?: Array<Record<string, { index_value?: { value?: CompassIndexValue } } | undefined>>;
}
export interface CompassCoreIndex {
  code?: string;
  msg?: string;
  data?: {
    module_data?: {
      homepage_core_index?: {
        compass_general_multi_index_card_value?: CompassCardValue;
      };
    };
  };
}

// 抖店 Compass API
export const compassApi = {
  getCoreIndex: () =>
    apiClient.get<ApiResponse<CompassCoreIndex>>('/external/compass/shop/core-index').then((res) => res.data?.data),
};

// ==================== 好货商品预览（外部抖音数据） ====================

// Haohuo 商品预览详情图片
export interface HaohuoDetailImage {
  uri: string;
  url_list: string[];
  width: number;
  height: number;
}

// Haohuo 商品预览新格式详情图片
export interface HaohuoDetailImageNew {
  image: HaohuoDetailImage;
  pic_type: string;
}

// Haohuo 商品预览规格格式
export interface HaohuoProductFormat {
  format: Array<{
    name: string;
    message: Array<{ desc: string }>;
    pic_urls: unknown;
    property_id: string;
  }>;
  media_elements: unknown;
}

// Haohuo 商品预览详情配置
export interface HaohuoDetailConfig {
  main_content: Array<{
    content: string[];
    type: number;
    title: string;
    links: Array<{ key: string; link: string }>;
    default_show: boolean;
  }>;
  main_title: string;
  main_type: number;
}

// Haohuo 商品预览标题图片
export interface HaohuoTitleImage {
  uri: string;
  url_list: string[];
  width: number;
  height: number;
}

// Haohuo 商品预览额外信息
export interface HaohuoExtra {
  logid: string;
  now: number;
  fatal_item_ids: string[];
}

// Haohuo 商品预览响应
export interface HaohuoProductPreview {
  status_code: number;
  detail_info: {
    detail_imgs: HaohuoDetailImage[];
    product_format: HaohuoProductFormat[];
    detail_config: HaohuoDetailConfig[];
    detail_imgs_new: HaohuoDetailImageNew[];
    title_image: HaohuoTitleImage;
    ai_question: unknown;
    tag_card: unknown;
    jump_url: string;
  };
  extra: HaohuoExtra;
  log_pb: { impr_id: string };
}

// 好货商品预览API
export const haohuoApi = {
  getProductPreview: (promotionId: string) =>
    apiClient.post<ApiResponse<HaohuoProductPreview>>('/external/haohuo/product/preview', { promotion_id: promotionId }).then((res) => res.data?.data),
};

// 导出认证辅助函数
export { setAuthToken, getAuthToken } from '@/utils/apiClient';

// 告警API
export const alertApi = {
  getConfig: () =>
    apiClient.get<ApiResponse<AlertConfig>>('/alerts/config').then((res) => res.data?.data),
  updateConfig: (config: AlertConfig) =>
    apiClient.post<ApiResponse<AlertConfig>>('/alerts/config', config).then((res) => res.data?.data),
  getHistory: (params?: Record<string, unknown>) =>
    apiClient.get<ApiResponse<PaginatedResponse<AlertHistoryItem>>>('/alerts/history', { params }).then((res) => res.data?.data),
  getStats: () =>
    apiClient.get<ApiResponse<AlertStats>>('/alerts/history/stats').then((res) => res.data?.data),
  clearHistory: () =>
    apiClient.post<ApiResponse<{ cleared: number }>>('/alerts/clear-history').then((res) => res.data?.data),
};

// Default export for backward compatibility
export default apiClient;