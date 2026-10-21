import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock apiClient before importing api modules
vi.mock('@/utils/apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  setAuthToken: vi.fn(),
  getAuthToken: vi.fn(() => null),
}));

// Mock config to avoid import.meta.env issues
vi.mock('@/utils/config', () => ({
  config: {
    apiBaseUrl: '',
    isDevelopment: false,
    isProduction: true,
    enableDevTools: false,
    logLevel: 'warn' as const,
  },
  log: vi.fn(),
}));

// Mock antd message
vi.mock('antd', () => ({
  message: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
    loading: vi.fn(),
  },
}));

import { apiClient } from '@/utils/apiClient';
import {
  productApi,
  orderApi,
  creatorApi,
  dashboardApi,
  alertApi,
  syncApi,
  healthApi,
  videoApi,
  accountApi,
  complianceApi,
  mediaApi,
  alertDouyinApi,
  alertDianApi,
  authApi,
} from './index';

const mockApi = apiClient as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

describe('API 模块', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('productApi', () => {
    it('getList 应调用 GET /products 并提取 data', async () => {
      const innerData = { data: [{ product_id: 'p1' }], total: 1, page: 1, size: 20 };
      const mockResponse = { data: { success: true, data: innerData } };
      mockApi.get.mockResolvedValue(mockResponse);

      const result = await productApi.getList({ page: 1 });

      expect(mockApi.get).toHaveBeenCalledWith('/products', {
        params: { page: 1 },
      });
      expect(result).toEqual(innerData);
    });

    it('getDetail 应调用 GET /products/:id', async () => {
      const innerData = { product_id: 'p1', product_name: 'Test' };
      const mockResponse = { data: { success: true, data: innerData } };
      mockApi.get.mockResolvedValue(mockResponse);

      const result = await productApi.getDetail('p1');

      expect(mockApi.get).toHaveBeenCalledWith('/products/p1');
      expect(result).toEqual(innerData);
    });
  });

  describe('orderApi', () => {
    it('getList 应调用 GET /orders', async () => {
      const innerData = { list: [], total: 0, page: 1, size: 20 };
      const mockResponse = { data: { success: true, data: innerData } };
      mockApi.get.mockResolvedValue(mockResponse);

      const result = await orderApi.getList({ status: 'completed' });

      expect(mockApi.get).toHaveBeenCalledWith('/orders', {
        params: { status: 'completed' },
      });
      expect(result).toEqual(innerData);
    });
  });

  describe('creatorApi', () => {
    it('getList 应调用 GET /creators', async () => {
      const innerData = { data: [], total: 0, page: 1, size: 20 };
      const mockResponse = { data: { success: true, data: innerData } };
      mockApi.get.mockResolvedValue(mockResponse);

      const result = await creatorApi.getList();

      expect(mockApi.get).toHaveBeenCalledWith('/creators', { params: undefined });
      expect(result).toEqual(innerData);
    });

    it('getDetail 应调用 GET /creators/:id', async () => {
      const innerData = { creator_id: 'c1' };
      const mockResponse = { data: { success: true, data: innerData } };
      mockApi.get.mockResolvedValue(mockResponse);

      const result = await creatorApi.getDetail('c1');

      expect(mockApi.get).toHaveBeenCalledWith('/creators/c1');
      expect(result).toEqual(innerData);
    });
  });

  describe('dashboardApi', () => {
    it('getStats 应调用 GET /dashboard/stats', async () => {
      const innerData = {
        total_sales_today: 100,
        total_sales_yesterday: 90,
        total_revenue_today: 1000,
        total_revenue_yesterday: 900,
        total_orders_today: 10,
        total_orders_yesterday: 9,
        avg_conversion_rate: 0.1,
        avg_conversion_rate_yesterday: 0.09,
        sales_trend: [],
        top_products: [],
      };
      const mockResponse = { data: { success: true, data: innerData } };
      mockApi.get.mockResolvedValue(mockResponse);

      const result = await dashboardApi.getStats();

      expect(mockApi.get).toHaveBeenCalledWith('/dashboard/stats', {
        params: undefined,
      });
      expect(result).toEqual(innerData);
    });

    it('getMockStatus 应调用 GET /mock/status', async () => {
      const innerData = {
        products: {
          is_mock: false,
          elapsed_minutes: 0,
          alert_threshold: 60,
          alert_triggered: false,
          alert_sent: false,
        },
        orders: {
          is_mock: false,
          elapsed_minutes: 0,
          alert_threshold: 60,
          alert_triggered: false,
          alert_sent: false,
        },
        creators: {
          is_mock: false,
          elapsed_minutes: 0,
          alert_threshold: 60,
          alert_triggered: false,
          alert_sent: false,
        },
      };
      const mockResponse = { data: { success: true, data: innerData } };
      mockApi.get.mockResolvedValue(mockResponse);

      const result = await dashboardApi.getMockStatus();

      expect(mockApi.get).toHaveBeenCalledWith('/mock/status');
      expect(result).toEqual(innerData);
    });
  });

  describe('alertApi', () => {
    it('getConfig 应调用 GET /alerts/config', async () => {
      const innerData = { enabled: true, sales_drop_threshold: 30 };
      const mockResponse = { data: { success: true, data: innerData } };
      mockApi.get.mockResolvedValue(mockResponse);

      const result = await alertApi.getConfig();

      expect(mockApi.get).toHaveBeenCalledWith('/alerts/config');
      expect(result).toEqual(innerData);
    });

    it('updateConfig 应调用 POST /alerts/config', async () => {
      const config = { enabled: false, sales_drop_threshold: 50 };
      const innerData = { enabled: false, sales_drop_threshold: 50 };
      const mockResponse = { data: { success: true, data: innerData } };
      mockApi.post.mockResolvedValue(mockResponse);

      const result = await alertApi.updateConfig(config);

      expect(mockApi.post).toHaveBeenCalledWith('/alerts/config', config);
      expect(result).toEqual(innerData);
    });
  });

  describe('syncApi', () => {
    it('manualSync 应调用 POST /sync/manual', async () => {
      const innerData = { last_update: '2026-08-25T10:00:00' };
      const mockResponse = { data: { success: true, data: innerData } };
      mockApi.post.mockResolvedValue(mockResponse);

      const result = await syncApi.manualSync();

      expect(mockApi.post).toHaveBeenCalledWith('/sync/manual', { params: { async: false } });
      expect(result).toEqual(innerData);
    });
  });

  describe('healthApi', () => {
    it('check 应调用 GET /health', async () => {
      const innerData = {
        status: 'healthy',
        timestamp: '2026-08-25T10:00:00',
        last_update: '2026-08-25T09:59:00',
      };
      const mockResponse = { data: { success: true, data: innerData } };
      mockApi.get.mockResolvedValue(mockResponse);

      const result = await healthApi.check();

      expect(mockApi.get).toHaveBeenCalledWith('/health');
      expect(result).toEqual(innerData);
    });

    it('getHealth 应与 check 调用相同端点', async () => {
      const innerData = { status: 'healthy', timestamp: '', last_update: null };
      const mockResponse = { data: { success: true, data: innerData } };
      mockApi.get.mockResolvedValue(mockResponse);

      await healthApi.getHealth();

      expect(mockApi.get).toHaveBeenCalledWith('/health');
    });
  });

  describe('videoApi', () => {
    it('getList 应调用 GET /videos', async () => {
      const mockResponse = {
        data: { data: [], total: 0, page: 1, size: 20 },
      };
      mockApi.get.mockResolvedValue(mockResponse);

      await videoApi.getList({ page: 2 });

      expect(mockApi.get).toHaveBeenCalledWith('/videos', {
        params: { page: 2 },
      });
    });

    it('create 应调用 POST /videos', async () => {
      const newVideo = { title: 'Test Video', creator_name: 'A' };
      const mockResponse = { data: { video_id: 'v1', ...newVideo } };
      mockApi.post.mockResolvedValue(mockResponse);

      await videoApi.create(newVideo);

      expect(mockApi.post).toHaveBeenCalledWith('/videos', newVideo);
    });

    it('delete 应调用 DELETE /videos/:id', async () => {
      mockApi.delete.mockResolvedValue({ data: null });

      await videoApi.delete('v1');

      expect(mockApi.delete).toHaveBeenCalledWith('/videos/v1');
    });
  });

  describe('accountApi', () => {
    it('getList 应调用 GET /accounts', async () => {
      const mockResponse = {
        data: { data: [], total: 0, page: 1, size: 20 },
      };
      mockApi.get.mockResolvedValue(mockResponse);

      await accountApi.getList();

      expect(mockApi.get).toHaveBeenCalledWith('/accounts', {
        params: undefined,
      });
    });

    it('update 应调用 PUT /accounts/:id', async () => {
      const updates = { account_name: 'Updated' };
      mockApi.put.mockResolvedValue({ data: { account_id: 'a1', ...updates } });

      await accountApi.update('a1', updates);

      expect(mockApi.put).toHaveBeenCalledWith('/accounts/a1', updates);
    });
  });

  describe('complianceApi', () => {
    it('getList 应调用 GET /compliance', async () => {
      const mockResponse = {
        data: { data: [], total: 0, page: 1, size: 20 },
      };
      mockApi.get.mockResolvedValue(mockResponse);

      await complianceApi.getList({ risk_level: 'high' });

      expect(mockApi.get).toHaveBeenCalledWith('/compliance', {
        params: { risk_level: 'high' },
      });
    });

    it('ignore 应调用 POST /compliance/:id/ignore', async () => {
      mockApi.post.mockResolvedValue({ data: { product_id: 'p1', status: 'ignored' } });

      await complianceApi.ignore('p1');

      expect(mockApi.post).toHaveBeenCalledWith('/compliance/p1/ignore');
    });

    it('takeDown 应调用 POST /compliance/:id/take-down', async () => {
      mockApi.post.mockResolvedValue({ data: {} });

      await complianceApi.takeDown('p1');

      expect(mockApi.post).toHaveBeenCalledWith('/compliance/p1/take-down');
    });

    it('restore 应调用 POST /compliance/:id/restore', async () => {
      mockApi.post.mockResolvedValue({ data: {} });

      await complianceApi.restore('p1');

      expect(mockApi.post).toHaveBeenCalledWith('/compliance/p1/restore');
    });
  });

  describe('mediaApi', () => {
    it('getVideoEditList 应调用 GET /media/video-edit', async () => {
      const mockResponse = {
        data: { data: [], total: 0, page: 1, size: 20 },
      };
      mockApi.get.mockResolvedValue(mockResponse);

      await mediaApi.getVideoEditList();

      expect(mockApi.get).toHaveBeenCalledWith('/media/video-edit', {
        params: undefined,
      });
    });

    it('getImageEditList 应调用 GET /media/image-edit', async () => {
      const mockResponse = {
        data: { data: [], total: 0, page: 1, size: 20 },
      };
      mockApi.get.mockResolvedValue(mockResponse);

      await mediaApi.getImageEditList();

      expect(mockApi.get).toHaveBeenCalledWith('/media/image-edit', {
        params: undefined,
      });
    });
  });

  describe('alertDouyinApi', () => {
    it('getConfig 应调用 GET /alerts/douyin/config', async () => {
      mockApi.get.mockResolvedValue({ data: { enabled: true } });

      await alertDouyinApi.getConfig();

      expect(mockApi.get).toHaveBeenCalledWith('/alerts/douyin/config');
    });

    it('updateConfig 应调用 POST /alerts/douyin/config', async () => {
      const config = { enabled: false };
      mockApi.post.mockResolvedValue({ data: config });

      await alertDouyinApi.updateConfig(config);

      expect(mockApi.post).toHaveBeenCalledWith('/alerts/douyin/config', config);
    });
  });

  describe('alertDianApi', () => {
    it('getConfig 应调用 GET /alerts/dian/config', async () => {
      mockApi.get.mockResolvedValue({ data: { enabled: true } });

      await alertDianApi.getConfig();

      expect(mockApi.get).toHaveBeenCalledWith('/alerts/dian/config');
    });

    it('updateConfig 应调用 POST /alerts/dian/config', async () => {
      const config = { enabled: false };
      mockApi.post.mockResolvedValue({ data: config });

      await alertDianApi.updateConfig(config);

      expect(mockApi.post).toHaveBeenCalledWith('/alerts/dian/config', config);
    });
  });

  describe('authApi', () => {
    it('getQrCode 应调用 GET /auth/qr-code 并提取 data', async () => {
      const innerData = { qr_code: 'data:image/png;base64,xxx' };
      const mockResponse = { data: { success: true, data: innerData } };
      mockApi.get.mockResolvedValue(mockResponse);

      const result = await authApi.getQrCode();

      expect(mockApi.get).toHaveBeenCalledWith('/auth/qr-code');
      expect(result).toEqual(innerData);
    });

    it('login 应调用 GET /auth/login 并提取 data', async () => {
      const innerData = { auth_url: 'https://example.com/auth' };
      const mockResponse = { data: { success: true, data: innerData } };
      mockApi.get.mockResolvedValue(mockResponse);

      const result = await authApi.login();

      expect(mockApi.get).toHaveBeenCalledWith('/auth/login');
      expect(result).toEqual(innerData);
    });

    it('getStatus 应调用 GET /auth/status 并提取 data', async () => {
      const innerData = { authorized: false, access_token: '', refresh_token: '' };
      const mockResponse = { data: { success: true, data: innerData } };
      mockApi.get.mockResolvedValue(mockResponse);

      const result = await authApi.getStatus();

      expect(mockApi.get).toHaveBeenCalledWith('/auth/status');
      expect(result).toEqual(innerData);
    });

    it('logout 应调用 POST /auth/logout', async () => {
      const mockResponse = { data: { success: true, data: null } };
      mockApi.post.mockResolvedValue(mockResponse);

      await authApi.logout();

      expect(mockApi.post).toHaveBeenCalledWith('/auth/logout');
    });
  });
});
