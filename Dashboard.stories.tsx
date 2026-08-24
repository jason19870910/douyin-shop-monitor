import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import Dashboard from '../pages/Dashboard';

// Mock data for stories
const mockStats = {
  total_sales_today: 12345,
  total_sales_yesterday: 11000,
  total_revenue_today: 567890.50,
  total_revenue_yesterday: 520000.00,
  total_orders_today: 567,
  total_orders_yesterday: 520,
  avg_conversion_rate: 0.032,
  avg_conversion_rate_yesterday: 0.028,
  sales_trend: [
    { date: '2026-08-12', sales: 1100 },
    { date: '2026-08-13', sales: 1150 },
    { date: '2026-08-14', sales: 1200 },
    { date: '2026-08-15', sales: 1180 },
    { date: '2026-08-16', sales: 1250 },
    { date: '2026-08-17', sales: 1300 },
    { date: '2026-08-18', sales: 1230 },
  ],
  top_products: [
    { product_id: 'P001', product_name: '爆款 T 恤', sales_today: 500, sales_yesterday: 450, inventory: 100, conversion_rate: 0.05 },
    { product_id: 'P002', product_name: '牛仔裤', sales_today: 380, sales_yesterday: 400, inventory: 50, conversion_rate: 0.04 },
    { product_id: 'P003', product_name: '运动鞋', sales_today: 320, sales_yesterday: 280, inventory: 200, conversion_rate: 0.035 },
    { product_id: 'P004', product_name: '卫衣', sales_today: 280, sales_yesterday: 300, inventory: 80, conversion_rate: 0.03 },
    { product_id: 'P005', product_name: '休闲裤', sales_today: 250, sales_yesterday: 220, inventory: 120, conversion_rate: 0.028 },
  ],
};

const mockProducts = {
  data: [
    { product_id: 'P001', product_name: '爆款 T 恤', sales_today: 500, sales_yesterday: 450, inventory: 100, conversion_rate: 0.05 },
    { product_id: 'P002', product_name: '牛仔裤', sales_today: 380, sales_yesterday: 400, inventory: 50, conversion_rate: 0.04 },
    { product_id: 'P003', product_name: '运动鞋', sales_today: 320, sales_yesterday: 280, inventory: 200, conversion_rate: 0.035 },
  ],
  total: 3,
};

const mockOrders = {
  data: [
    { order_id: 'O001', product_name: '爆款 T 恤', amount: 199.00, status: 'completed', create_time: '2026-08-18 10:30:00' },
    { order_id: 'O002', product_name: '牛仔裤', amount: 299.00, status: 'pending', create_time: '2026-08-18 10:25:00' },
    { order_id: 'O003', product_name: '运动鞋', amount: 599.00, status: 'completed', create_time: '2026-08-18 10:20:00' },
  ],
  total: 3,
};

// Mock useApi hook for stories
const mockUseApi = <T>(data: T) => ({
  data: { data },
  loading: false,
  error: null,
  refetch: () => Promise.resolve(data),
});

// We'll use a wrapper to provide mocked context
const DashboardWrapper: React.FC<{ 
  stats?: typeof mockStats;
  products?: typeof mockProducts;
  orders?: typeof mockOrders;
  loading?: boolean;
  error?: Error | null;
}> = ({ 
  stats = mockStats, 
  products = mockProducts, 
  orders = mockOrders,
  loading = false,
  error = null 
}) => {
  // Since Dashboard uses hooks internally, we'll render a simplified version for stories
  return (
    <ConfigProvider locale={zhCN}>
      <div style={{ padding: 24, background: '#f0f2f5', minHeight: '100vh' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <DashboardPreview 
            stats={stats} 
            products={products} 
            orders={orders}
            loading={loading}
            error={error}
          />
        </div>
      </ConfigProvider>
  );
};

// Simplified preview component that mimics Dashboard structure
const DashboardPreview: React.FC<{
  stats: typeof mockStats;
  products: typeof mockProducts;
  orders: typeof mockOrders;
  loading: boolean;
  error: Error | null;
}> = ({ stats, products, orders, loading, error }) => {
  const { formatNumber, formatCurrency, formatPercent } = require('../utils/formatters');
  
  const salesTrend = stats.sales_trend;
  const topProducts = stats.top_products;
  const productsData = products.data;
  const ordersData = orders.data;

  if (loading) return <div style={{ textAlign: 'center', padding: 48 }}>加载中...</div>;
  if (error) return <div style={{ color: '#ff4d4f', textAlign: 'center', padding: 48 }}>加载失败: {error.message}</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>📊 仪表盘</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <button style={{ padding: '8px 16px', background: '#1890ff', color: '#fff', border: 'none', borderRadius: 4 }}>立即同步</button>
          <button style={{ padding: '8px 16px', border: '1px solid #d9d9d9', borderRadius: 4 }}>导出 CSV</button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16, marginBottom: 24 }}>
        <StatCard label="今日总销量" value={formatNumber(stats.total_sales_today)} trend={((stats.total_sales_today - stats.total_sales_yesterday) / stats.total_sales_yesterday * 100)} trendLabel="较昨日" icon="📦" />
        <StatCard label="今日总收入" value={formatCurrency(stats.total_revenue_today)} prefix="¥" trend={((stats.total_revenue_today - stats.total_revenue_yesterday) / stats.total_revenue_yesterday * 100)} trendLabel="较昨日" icon="💰" />
        <StatCard label="今日订单数" value={formatNumber(stats.total_orders_today)} trend={((stats.total_orders_today - stats.total_orders_yesterday) / stats.total_orders_yesterday * 100)} trendLabel="较昨日" icon="🛒" />
        <StatCard label="平均转化率" value={formatPercent(stats.avg_conversion_rate)} trend={((stats.avg_conversion_rate - stats.avg_conversion_rate_yesterday) / stats.avg_conversion_rate_yesterday * 100)} trendLabel="较昨日" icon="📊" />
      </div>

      {/* 销售趋势图 */}
      <div style={{ background: '#fff', borderRadius: 8, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: 24 }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600 }}>销售趋势 (近7天)</h3>
        <div style={{ height: 200, display: 'flex', alignItems: 'flex-end', gap: 8, paddingBottom: 20 }}>
          {salesTrend.map((item, index) => (
            <div key={index} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div 
                style={{ 
                  width: '100%', 
                  height: `${Math.max(10, (item.sales / Math.max(...salesTrend.map(d => d.sales))) * 180)}px`,
                  background: 'linear-gradient(180deg, #1890ff 0%, #40a9ff 100%)',
                  borderRadius: '4px 4px 0 0',
                  transition: 'height 0.3s',
                }}
              />
              <span style={{ fontSize: 10, color: '#999', marginTop: 4 }}>{item.date.slice(5)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 热销商品 TOP 5 */}
      <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: 24 }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between' }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>热销商品 TOP 5</h3>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#fafafa' }}>
                <th style={{ padding: '12px 16px', textAlign: 'left', borderBottom: '1px solid #f0f0f0', fontWeight: 600 }}>排名</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', borderBottom: '1px solid #f0f0f0', fontWeight: 600 }}>商品名称</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', borderBottom: '1px solid #f0f0f0', fontWeight: 600 }}>今日销量</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', borderBottom: '1px solid #f0f0f0', fontWeight: 600 }}>昨日销量</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', borderBottom: '1px solid #f0f0f0', fontWeight: 600 }}>增长率</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', borderBottom: '1px solid #f0f0f0', fontWeight: 600 }}>库存</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', borderBottom: '1px solid #f0f0f0', fontWeight: 600 }}>转化率</th>
              </tr>
            </thead>
            <tbody>
              {topProducts.slice(0, 5).map((product, index) => {
                const growth = ((product.sales_today - product.sales_yesterday) / (product.sales_yesterday || 1) * 100);
                return (
                  <tr key={product.product_id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 600, color: '#1890ff' }}>{index + 1}</td>
                    <td style={{ padding: '12px 16px' }}>{product.product_name}</td>
                    <td style={{ padding: '12px 16px', textAlign: 'right', color: '#1890ff', fontWeight: 500 }}>{product.sales_today.toLocaleString()}</td>
                    <td style={{ padding: '12px 16px', textAlign: 'right', color: '#999' }}>{product.sales_yesterday.toLocaleString()}</td>
                    <td style={{ padding: '12px 16px', textAlign: 'right', color: growth > 0 ? '#ff4d4f' : growth < 0 ? '#52c41a' : '#999', fontWeight: 500 }}>
                      {growth > 0 ? '↑' : growth < 0 ? '↓' : '→'} {Math.abs(growth).toFixed(1)}%
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right', color: product.inventory <= 10 ? '#ff4d4f' : '#595959' }}>
                      {product.inventory.toLocaleString()}
                      {product.inventory <= 10 && <span style={{ marginLeft: 4, color: '#ff4d4f', fontSize: 10 }}>⚠ 低库存</span>}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right' }}>{(product.conversion_rate * 100).toFixed(2)}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 订单看板 */}
      <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between' }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>最新订单 TOP 5</h3>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#fafafa' }}>
                <th style={{ padding: '12px 16px', textAlign: 'left', borderBottom: '1px solid #f0f0f0', fontWeight: 600 }}>订单ID</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', borderBottom: '1px solid #f0f0f0', fontWeight: 600 }}>商品名称</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', borderBottom: '1px solid #f0f0f0', fontWeight: 600 }}>金额</th>
                <th style={{ padding: '12px 16px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', fontWeight: 600 }}>状态</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', borderBottom: '1px solid #f0f0f0', fontWeight: 600 }}>下单时间</th>
              </tr>
            </thead>
            <tbody>
              {ordersData.slice(0, 5).map((order) => (
                <tr key={order.order_id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '12px 16px', fontFamily: 'monospace' }}>{order.order_id}</td>
                  <td style={{ padding: '12px 16px' }}>{order.product_name}</td>
                  <td style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 500 }}>¥{order.amount.toFixed(2)}</td>
                  <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      background: order.status === 'completed' ? '#f6ffed' : '#fffbe6',
                      color: order.status === 'completed' ? '#52c41a' : '#faad14',
                    }}>
                      {order.status === 'completed' ? '已完成' : '待处理'}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', color: '#999' }}>{order.create_time}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Simple StatCard for preview
const StatCard: React.FC<{
  label: string;
  value: string;
  trend: number;
  trendLabel: string;
  prefix?: string;
  icon?: string;
}> = ({ label, value, trend, trendLabel, prefix, icon }) => (
  <div style={{ background: '#fff', borderRadius: 8, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', borderTop: trend > 0 ? '3px solid #ff4d4f' : trend < 0 ? '3px solid #52c41a' : 'none' }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
      {icon && <span style={{ fontSize: 16 }}>{icon}</span>}
      <span style={{ fontSize: 14, color: '#8c8c8c' }}>{label}</span>
    </div>
    <div style={{ fontSize: 28, fontWeight: 600, color: '#1a1a1a' }}>
      {prefix}{value}
    </div>
    <div style={{ marginTop: 8, fontSize: 12, color: trend > 0 ? '#ff4d4f' : trend < 0 ? '#52c41a' : '#8c8c8c' }}>
      {trend > 0 ? '↑' : trend < 0 ? '↓' : '→'} {Math.abs(trend).toFixed(1)}% {trendLabel}
    </div>
  </div>
);

const meta: Meta<typeof DashboardWrapper> = {
  title: 'Pages/Dashboard',
  component: DashboardWrapper,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <ConfigProvider locale={zhCN}>
        <Story />
      </ConfigProvider>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof DashboardWrapper>;

export const Default: Story = {
  args: {},
};

export const Loading: Story = {
  args: {
    loading: true,
  },
};

export const WithError: Story = {
  args: {
    error: new Error('网络请求失败，请检查连接'),
    loading: false,
  },
};

export const EmptyData: Story = {
  args: {
    loading: false,
    stats: {
      ...mockStats,
      total_sales_today: 0,
      total_sales_yesterday: 0,
      total_revenue_today: 0,
      total_revenue_yesterday: 0,
      total_orders_today: 0,
      total_orders_yesterday: 0,
      avg_conversion_rate: 0,
      avg_conversion_rate_yesterday: 0,
      sales_trend: [],
      top_products: [],
    },
    products: { data: [], total: 0 },
    orders: { data: [], total: 0 },
  },
};

export const HighGrowth: Story = {
  args: {
    stats: {
      ...mockStats,
      total_sales_today: 20000,
      total_sales_yesterday: 10000,
      total_revenue_today: 1000000,
      total_revenue_yesterday: 500000,
      total_orders_today: 1000,
      total_orders_yesterday: 500,
      avg_conversion_rate: 0.05,
      avg_conversion_rate_yesterday: 0.025,
    },
  },
};

export const LowInventory: Story = {
  args: {
    stats: {
      ...mockStats,
      top_products: [
        { product_id: 'P001', product_name: '爆款 T 恤', sales_today: 500, sales_yesterday: 450, inventory: 5, conversion_rate: 0.05 },
        { product_id: 'P002', product_name: '牛仔裤', sales_today: 380, sales_yesterday: 400, inventory: 2, conversion_rate: 0.04 },
      ],
    },
  },
};