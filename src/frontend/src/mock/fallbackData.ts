/**
 * 当后端返回 503/401 时使用的本地默认数据（兜底数据）。
 * 通过环境变量 VITE_ENABLE_MOCK_FALLBACK 控制是否启用。
 */
import type { DashboardStats, MockStatus, HealthResponse, DashboardStatsResponse, MockStatusResponse } from '@/api/index';

// 统计数据的默认占位符（所有数值均为 0，避免 UI 报错）
export const fallbackDashboardStats: DashboardStats = {
  total_sales_today: 0,
  total_sales_yesterday: 0,
  total_revenue_today: 0,
  total_revenue_yesterday: 0,
  total_orders_today: 0,
  total_orders_yesterday: 0,
  avg_conversion_rate: 0,
  avg_conversion_rate_yesterday: 0,
  sales_trend: [],
  revenue_trend: [],
  order_trend: [],
  top_products: [],
  data_source: 'mock',
};

// Mock 状态的默认占位符
export const fallbackMockStatus: MockStatus = {
  products: {
    is_mock: true,
    elapsed_minutes: 0,
    alert_threshold: 60,
    alert_triggered: false,
    alert_sent: false,
  },
  orders: {
    is_mock: true,
    elapsed_minutes: 0,
    alert_threshold: 60,
    alert_triggered: false,
    alert_sent: false,
  },
  creators: {
    is_mock: true,
    elapsed_minutes: 0,
    alert_threshold: 60,
    alert_triggered: false,
    alert_sent: false,
  },
};

// 健康检查的默认占位符
export const fallbackHealthResponse: HealthResponse = {
  status: 'mock',
  timestamp: new Date().toISOString(),
  last_update: new Date().toISOString(),
};

// 环境变量检查工具
export const isMockFallbackEnabled = (): boolean => {
  return import.meta.env.VITE_ENABLE_MOCK_FALLBACK === 'true';
};

// 创建 mock 响应包装器，匹配后端返回的结构 (DashboardStatsResponse = { data: DashboardStats; data_source?: 'real' | 'mock' })
export const createMockStatsResponse = (): DashboardStatsResponse => ({
  data: fallbackDashboardStats,
  data_source: 'mock',
});

export const createMockStatusResponse = (): MockStatusResponse => ({
  data: fallbackMockStatus,
});

export const createMockHealthResponse = (): HealthResponse => ({
  ...fallbackHealthResponse,
});
