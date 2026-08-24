import React, { useState, useCallback, useMemo } from 'react';
import dayjs from 'dayjs';
import type { Product, Order, Creator, PaginatedResponse, DashboardStatsResponse, OrderListResponse, MockStatusItem, MockStatusResponse, HealthResponse } from '@/api/index';
import { Card, Row, Col, Spin, Alert, Button, Table, Tag, Space, DatePicker, Radio, message, Typography } from 'antd';
import {
  ShoppingOutlined,
  ShoppingCartOutlined,
  SettingOutlined,
  DollarOutlined,
  DownloadOutlined,
  ReloadOutlined,
  AlertOutlined,
  WarningOutlined,
  TeamOutlined,
  LineChartOutlined,
  PieChartOutlined,
} from '@ant-design/icons';
import { dashboardApi, healthApi, productApi, orderApi, creatorApi } from '@/api/index';
import { useApi, usePolling } from '@/hooks/useApi';
import { formatNumber, formatCurrency, formatPercent, formatDateTime, calculateGrowth, getTrendClass } from '@/utils/formatters';
import {
  ResponsiveContainer,
  BarChart,
  LineChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Line,
  Bar,
  Legend,
} from 'recharts';
import { PageContainer, PageHeader, TableCard } from '@/components/layout';
import { MetricCard, OrderStatusDistribution, OrderTrendMiniChart, SkeletonCard, CreatorDataCard } from '@/components/dashboard';
import { NormalizedError } from '@/utils/apiClient';
import styles from './Dashboard.module.css';

const { Title, Text } = Typography;

interface TrendChartData {
  date: string;
  sales?: number;
  revenue?: number;
  orders?: number;
  conversion?: number;
}

interface TrendChartProps {
  data: TrendChartData[];
  metric: 'sales' | 'revenue' | 'orders' | 'conversion';
  title: string;
  color: string;
  formatter?: (value: number) => string;
}

const TrendChart = ({ data, metric, title, color, formatter }: TrendChartProps) => {
  if (!data || data.length === 0) return null;

  const chartData = data.map(d => ({
    date: d.date,
    value: d[metric] ?? 0,
  }));

  const MetricChart = metric === 'conversion' ? LineChart : BarChart;

  return (
    <Card className={styles.chartCard}>
      <div className={styles.chartTitle}>
        <span>{title}</span>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <MetricChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
          <XAxis dataKey="date" stroke="var(--color-text-tertiary)" fontSize={12} tick={{ fill: 'var(--color-text-tertiary)' }} />
          <YAxis stroke="var(--color-text-tertiary)" fontSize={12} tickFormatter={(value: number) => formatter ? formatter(value) : formatNumber(value)} tick={{ fill: 'var(--color-text-tertiary)' }} />
          <Tooltip 
            formatter={(value: number) => [formatter ? formatter(value) : formatNumber(value), title]} 
            labelFormatter={(date: string) => `日期: ${date}`}
          />
          <Legend />
          {metric === 'conversion' ? (
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              dot={{ fill: color, strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6 }}
            />
          ) : (
            <Bar
              dataKey="value"
              fill={color}
              radius={[4, 4, 0, 0]}
              barSize={40}
            />
          )}
        </MetricChart>
      </ResponsiveContainer>
    </Card>
  );
};

const { RangePicker } = DatePicker;

const Dashboard = () => {
  const [selectedPeriod, setSelectedPeriod] = useState('7d');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [refreshLoading, setRefreshLoading] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);

  // 获取仪表盘统计数据
  const { data: statsResponse, status: statsStatus, error: statsError, refetch: refetchStats } = useApi<DashboardStatsResponse>(
    () => dashboardApi.getStats({ period: selectedPeriod }),
    [selectedPeriod],
    { retryOnError: true }
  );
  const statsLoading = statsStatus === 'loading';

  // 获取商品列表
  const { data: products, status: productsStatus, error: productsError, refetch: refetchProducts } = useApi<PaginatedResponse<Product>>(
    useCallback(() => productApi.getList({ page: 1, size: 10 }), []),
    [],
    { retryOnError: true }
  );
  const productsLoading = productsStatus === 'loading';

  // 获取订单列表
  const { data: ordersResponse, status: ordersStatus, error: ordersError, refetch: refetchOrders } = useApi<OrderListResponse>(
    useCallback(() => orderApi.getList({ page: 1, size: 50 }), []),
    [],
    { retryOnError: true }
  );
  const ordersLoading = ordersStatus === 'loading';

  // 获取创作者数据
  const { data: creatorsResponse, status: creatorsStatus, refetch: refetchCreators } = useApi<PaginatedResponse<Creator>>(
    useCallback(() => creatorApi.getList({ page: 1, size: 10 }), []),
    [],
    { retryOnError: true }
  );
  const creatorsLoading = creatorsStatus === 'loading';

  // Mock 状态轮询
  const { data: mockStatusResponse, status: mockStatusStatus } = usePolling<MockStatusResponse>(
    () => dashboardApi.getMockStatus(),
    30000,
    { retryOnError: true }
  );
  const mockStatusLoading = mockStatusStatus === 'loading';

  // 健康检查轮询
  const { data: healthData, status: healthStatus } = usePolling<HealthResponse>(
    () => healthApi.getHealth(),
    60000,
    { retryOnError: true }
  );
  const healthLoading = healthStatus === 'loading';

  // 判断是否使用模拟数据
  const isMockData = statsResponse?.data_source === 'mock' || 
                     products?.data_source === 'mock' || 
                     ordersResponse?.data_source === 'mock';

  // 告警状态
  const mockAlerts = mockStatusResponse?.data;
  const hasActiveAlert = mockAlerts && Object.values(mockAlerts || {}).some((item: MockStatusItem) => item.alert_triggered);

  const handleRefresh = async () => {
    setRefreshLoading(true);
    setLastRefreshed(new Date());
    await Promise.all([
      refetchStats(),
      refetchProducts(),
      refetchOrders(),
      refetchCreators(),
    ]);
    setRefreshLoading(false);
  };

  const handlePeriodChange = (period: string) => {
    setSelectedPeriod(period);
  };

  const handleDateChange = (dates: [dayjs.Dayjs, dayjs.Dayjs]) => {
    setDateRange(dates);
  };

  const handleExportDashboard = async () => {
    try {
      message.loading('导出中...', 0);
      const statsResult = await refetchStats();
      const productsResult = await refetchProducts();
      const ordersResult = await refetchOrders();
      message.destroy();

      const statsData = statsResult?.data || statsResponse?.data;
      const productsData = productsResult?.data || products?.data || [];
      const ordersData = ordersResult?.list || ordersResponse?.list || [];

      const csvContent = [
        ['指标', '今日', '昨日', '增长率'],
        ['总销量', statsData?.total_sales_today || 0, statsData?.total_sales_yesterday || 0, calculateGrowth(statsData?.total_sales_today || 0, statsData?.total_sales_yesterday || 0).toFixed(1) + '%'],
        ['总收入', statsData?.total_revenue_today || 0, statsData?.total_revenue_yesterday || 0, calculateGrowth(statsData?.total_revenue_today || 0, statsData?.total_revenue_yesterday || 0).toFixed(1) + '%'],
        ['订单数', statsData?.total_orders_today || 0, statsData?.total_orders_yesterday || 0, calculateGrowth(statsData?.total_orders_today || 0, statsData?.total_orders_yesterday || 0).toFixed(1) + '%'],
        ['转化率', statsData?.avg_conversion_rate || 0, statsData?.avg_conversion_rate_yesterday || 0, calculateGrowth(statsData?.avg_conversion_rate || 0, statsData?.avg_conversion_rate_yesterday || 0).toFixed(1) + '%'],
        ['', '', '', ''],
        ['热销商品 TOP 10', '', '', ''],
        ['商品ID', '商品名称', '今日销量', '昨日销量', '库存', '转化率'],
        ...(statsData?.top_products || []).slice(0, 10).map(p => [
          p.product_id,
          p.product_name,
          p.sales_today,
          p.sales_yesterday,
          p.inventory,
          formatPercent(p.conversion_rate),
        ]),
        ['', '', '', ''],
        ['最新订单 TOP 10', '', '', ''],
        ['订单ID', '商品名称', '金额', '状态', '下单时间'],
        ...(ordersData || []).slice(0, 10).map(o => [
          o.order_id,
          o.product_name,
          o.amount,
          o.status,
          o.create_time,
        ]),
      ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `dashboard_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      message.success('导出成功');
    } catch (err) {
      message.destroy();
      message.error('导出失败');
    }
  };

  // 计算统计
  const statsData = statsResponse?.data;
  const totalSales = statsData?.total_sales_today || 0;
  const totalRevenue = statsData?.total_revenue_today || 0;
  const totalOrders = statsData?.total_orders_today || 0;
  const avgConversion = statsData?.avg_conversion_rate || 0;
  const salesYesterday = statsData?.total_sales_yesterday || 0;
  const revenueYesterday = statsData?.total_revenue_yesterday || 0;
  const ordersYesterday = statsData?.total_orders_yesterday || 0;
  const conversionYesterday = statsData?.avg_conversion_rate_yesterday || 0;

  const salesTrend = statsData?.sales_trend || [];
  const topProducts = statsData?.top_products || [];

  const productsData = products?.data || [];
  const productsTotal = products?.total || 0;

  const ordersData = ordersResponse?.list || [];
  const ordersTotal = ordersResponse?.total || 0;

  // 创作者数据计算
  const creatorsData = creatorsResponse?.data || [];
  const totalFollowers = creatorsData.reduce((sum: number, c: Creator) => sum + (Number(c.followers) || Number(c.follower_count) || 0), 0);
  const todayNewFollowers = creatorsData.reduce((sum: number, c: Creator) => sum + (Number(c.today_new_followers) || 0), 0);
  const avgEngagementRate = creatorsData.length > 0
    ? creatorsData.reduce((sum: number, c: Creator) => sum + (Number(c.avg_conversion_rate) || 0), 0) / creatorsData.length
    : 0;

  // 生成创作者趋势模拟数据（基于粉丝总数模拟增长）
  const creatorTrendData = useMemo(() => 
    salesTrend.map(d => ({ 
      date: d.date, 
      followers: Math.round(totalFollowers * (0.98 + 0.04 * ((d.date.charCodeAt(0) % 100) / 100)))
    }))
  , [salesTrend, totalFollowers]);

  // 生成订单趋势数据
  const orderTrendData = useMemo(() => 
    salesTrend.map(d => ({ 
      date: d.date, 
      count: Math.round((d.sales || 0) * 0.5)
    }))
  , [salesTrend]);

  // 转化率趋势数据（模拟波动，避免在渲染中使用 Math.random）
  const conversionTrendData = useMemo(() => 
    salesTrend.map(d => ({ 
      date: d.date, 
      conversion: (statsData?.avg_conversion_rate || 0) * (0.9 + 0.2 * ((d.date.charCodeAt(0) % 100) / 100))
    }))
  , [salesTrend, statsData]);

  const periodOptions = [
    { value: '7d', label: '近 7 天' },
    { value: '30d', label: '近 30 天' },
    { value: '90d', label: '近 90 天' },
  ];

  const statusMap = {
    'completed': { color: 'green', text: '已完成' },
    'pending': { color: 'orange', text: '待处理' },
    'cancelled': { color: 'red', text: '已取消' },
    'refunded': { color: 'blue', text: '已退款' },
  };

  // 确定各区域的加载状态
  const metricsLoading = statsLoading;
  const chartsLoading = statsLoading;
  const productsSectionLoading = productsLoading;
  const ordersSectionLoading = ordersLoading;
  const creatorsSectionLoading = creatorsLoading;

  return (
    <PageContainer>
      <PageHeader
        title={<span style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-3)' }}><Title level={3} style={{ margin: 0 }}>📊 仪表盘</Title></span>}
        actions={
          <Space wrap className={styles.headerActions}>
            <RangePicker
              value={dateRange}
              onChange={handleDateChange}
              placeholder={['开始日期', '结束日期']}
              style={{ width: 300 }}
              allowClear
            />
            <Button icon={<DownloadOutlined />} onClick={handleExportDashboard} type="default">
              导出 CSV
            </Button>
            <Button icon={<ReloadOutlined />} onClick={handleRefresh} loading={refreshLoading}>
              立即同步
            </Button>
          </Space>
        }
        filters={
          <Radio.Group value={selectedPeriod} onChange={e => handlePeriodChange(e.target.value)} className={styles.periodSelector}>
            {periodOptions.map(opt => (
              <Radio.Button key={opt.value} value={opt.value}>{opt.label}</Radio.Button>
            ))}
          </Radio.Group>
        }
      />

      {/* 最后更新时间 */}
      <div className={styles.lastUpdated}>
        {lastRefreshed && <span>最后刷新: {formatDateTime(lastRefreshed.toISOString())}</span>}
        {healthData?.last_update && <span style={{ marginLeft: 'var(--spacing-4)' }}>数据更新: {formatDateTime(healthData.last_update)}</span>}
        {isMockData && (
          <Tag color="orange" style={{ marginLeft: 'var(--spacing-4)', fontSize: 'var(--font-size-xs)' }}>
            ⚠ 当前显示模拟数据（外部 API 暂无数据）
          </Tag>
        )}
        {!isMockData && healthData?.last_update && (
          <Tag color="green" style={{ marginLeft: 'var(--spacing-4)', fontSize: 'var(--font-size-xs)' }}>
            ✓ 实时数据
          </Tag>
        )}
      </div>

      {/* Mock 告警展示 */}
      {hasActiveAlert && mockAlerts && (
        <Alert
          message="数据源告警"
          description={
            <Space direction="vertical" style={{ width: '100%' }}>
              {Object.entries(mockAlerts || {}).map(([key, item]: [string, MockStatusItem]) => (
                item.alert_triggered && (
                  <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-2)', padding: 'var(--spacing-2) 0' }}>
                    <WarningOutlined style={{ color: 'var(--color-error-500)', fontSize: 16 }} />
                    <span>
                      <strong>{key === 'products' ? '商品' : key === 'orders' ? '订单' : '创作者'}数据源</strong>
                      {' '}持续使用模拟数据 <strong>{item.elapsed_minutes} 分钟</strong>
                      （阈值: {item.alert_threshold} 分钟）
                      {item.alert_sent && <Tag color="red" style={{ marginLeft: 'var(--spacing-2)' }}>告警已发送</Tag>}
                    </span>
                  </div>
                )
              ))}
              <div style={{ marginTop: 'var(--spacing-2)', padding: 'var(--spacing-2)', background: '#fff7e6', borderRadius: 'var(--radius-sm)' }}>
                <AlertOutlined style={{ marginRight: 'var(--spacing-2)' }} />
                <span>建议：登录抖店/创作者中心重新获取 Cookie 和签名参数，更新服务器配置后重启服务</span>
              </div>
            </Space>
          }
          type="error"
          showIcon
          closable
        />
      )}

      {/* 核心指标卡片区 - 响应式网格布局 */}
      <div className={styles.metricsGrid}>
        <MetricCard
          label="总销量"
          value={formatNumber(totalSales)}
          trend={calculateGrowth(totalSales, salesYesterday)}
          trendLabel="vs 昨日"
          icon={<ShoppingOutlined />}
          loading={metricsLoading}
        />
        <MetricCard
          label="总收入"
          value={formatCurrency(totalRevenue).replace('¥', '')}
          prefix="¥"
          trend={calculateGrowth(totalRevenue, revenueYesterday)}
          trendLabel="vs 昨日"
          icon={<DollarOutlined />}
          loading={metricsLoading}
        />
        <MetricCard
          label="订单数"
          value={formatNumber(totalOrders)}
          trend={calculateGrowth(totalOrders, ordersYesterday)}
          trendLabel="vs 昨日"
          icon={<ShoppingCartOutlined />}
          loading={metricsLoading}
        />
        <MetricCard
          label="转化率"
          value={formatPercent(avgConversion)}
          trend={calculateGrowth(avgConversion, conversionYesterday)}
          trendLabel="vs 昨日"
          icon={<SettingOutlined />}
          loading={metricsLoading}
        />
        <MetricCard
          label="商品总数"
          value={formatNumber(productsTotal)}
          trend={productsData.length > 0 ? 5 : 0}
          trendLabel="在售商品"
          icon={<TeamOutlined />}
          loading={metricsLoading}
        />
        <MetricCard
          label="创作者粉丝"
          value={formatNumber(totalFollowers)}
          trend={todayNewFollowers > 0 ? Math.round((todayNewFollowers / Math.max(totalFollowers - todayNewFollowers, 1)) * 100) : 0}
          trendLabel="今日新增"
          icon={<TeamOutlined />}
          loading={metricsLoading}
        />
      </div>

      {/* 趋势图表区域 - 响应式网格 */}
      <div className={styles.chartsGrid}>
        <div className={styles.chartWrapper}>
          <TrendChart
            data={salesTrend}
            metric="sales"
            title="销量趋势"
            color="var(--color-primary-500)"
            formatter={formatNumber}
          />
        </div>
        <div className={styles.chartWrapper}>
          <TrendChart
            data={salesTrend.map(d => ({ date: d.date, revenue: d.sales * 100 }))}
            metric="revenue"
            title="收入趋势"
            color="var(--color-success-500)"
            formatter={v => formatCurrency(v).replace('¥', '')}
          />
        </div>
        <div className={styles.chartWrapper}>
          <TrendChart
            data={salesTrend.map(d => ({ date: d.date, orders: Math.round(d.sales / 2) }))}
            metric="orders"
            title="订单趋势"
            color="var(--color-primary-700)"
            formatter={formatNumber}
          />
        </div>
        <div className={styles.chartWrapper}>
          <TrendChart
            data={conversionTrendData}
            metric="conversion"
            title="转化率趋势"
            color="var(--color-warning-500)"
            formatter={formatPercent}
          />
        </div>
      </div>

      {/* 商品与订单并列区域 - 响应式 2/1 列布局 */}
      <div className={styles.sectionGrid}>
        {/* 商品数据区 */}
        <div className={styles.sectionCard}>
          <div className={styles.sectionHeader}>
            <Title level={4} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--spacing-2)' }}>
              <ShoppingOutlined style={{ color: 'var(--color-primary-500)' }} />
              热销商品 TOP 10
            </Title>
            <Space>
              <Button type="link" size="small" onClick={() => refetchProducts()}>刷新</Button>
              <Button type="link" size="small" onClick={() => refetchProducts()}>查看全部</Button>
            </Space>
          </div>
          <TableCard<Product>
            dataSource={topProducts.slice(0, 10)}
            columns={[
              { title: '排名', key: 'rank', width: 60, render: (_, __, index) => <strong>{index + 1}</strong> },
              { title: '商品ID', dataIndex: 'product_id', key: 'product_id', width: 120 },
              { title: '商品名称', dataIndex: 'product_name', key: 'product_name', ellipsis: true, width: 200 },
              { title: '今日销量', dataIndex: 'sales_today', key: 'sales_today', align: 'right' as const, width: 100, render: formatNumber },
              { title: '昨日销量', dataIndex: 'sales_yesterday', key: 'sales_yesterday', align: 'right' as const, width: 100, render: formatNumber },
              { title: '增长率', key: 'growth', align: 'right' as const, width: 100, render: (_, record: Product) => {
                const growth = calculateGrowth(record.sales_today || 0, record.sales_yesterday || 0);
                const cls = getTrendClass(record.sales_today || 0, record.sales_yesterday || 0);
                return <span className={`${styles.growth} ${cls}`}>{growth > 0 ? '↑' : growth < 0 ? '↓' : '→'} {Math.abs(growth).toFixed(1)}%</span>;
              }},
              { title: '库存', dataIndex: 'inventory', key: 'inventory', align: 'right' as const, width: 100, render: (v) => v <= 10 ? <Tag color="red">{formatNumber(v)}</Tag> : formatNumber(v) },
              { title: '转化率', dataIndex: 'conversion_rate', key: 'conversion_rate', align: 'right' as const, width: 100, render: formatPercent },
            ]}
            rowKey="product_id"
            pagination={false}
            size="middle"
            loading={productsSectionLoading}
            error={productsError}
          />
        </div>

        {/* 订单数据区 */}
        <div className={styles.sectionCard}>
          <div className={styles.sectionHeader}>
            <Title level={4} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--spacing-2)' }}>
              <ShoppingCartOutlined style={{ color: 'var(--color-success-500)' }} />
              订单看板
            </Title>
            <Space>
              <Button type="link" size="small" onClick={() => refetchOrders()}>刷新</Button>
              <Button type="link" size="small">查看全部</Button>
            </Space>
          </div>
          
          {/* 订单概览指标 */}
          <div className={styles.orderMetricsGrid}>
            <MetricCard
              label="今日订单"
              value={formatNumber(ordersData.filter(o => o.create_time?.startsWith(new Date().toISOString().split('T')[0])).length || ordersData.length)}
              icon={<ShoppingCartOutlined />}
              loading={ordersSectionLoading}
            />
            <MetricCard
              label="今日成交额"
              value={formatCurrency(ordersData.filter(o => o.create_time?.startsWith(new Date().toISOString().split('T')[0])).reduce((sum, o) => sum + (o.amount || 0), 0) || ordersData.reduce((sum, o) => sum + (o.amount || 0), 0))}
              prefix="¥"
              icon={<DollarOutlined />}
              loading={ordersSectionLoading}
            />
            <MetricCard
              label="平均客单价"
              value={ordersData.length > 0 ? formatCurrency(ordersData.reduce((sum, o) => sum + (o.amount || 0), 0) / ordersData.length) : '¥0'}
              prefix="¥"
              icon={<SettingOutlined />}
              loading={ordersSectionLoading}
            />
          </div>

          {/* 订单状态分布 + 趋势 */}
          <div className={styles.orderChartsGrid}>
            <div className={styles.chartWrapper}>
              <OrderStatusDistribution data={ordersData} loading={ordersSectionLoading} />
            </div>
            <div className={styles.chartWrapper}>
              <OrderTrendMiniChart data={orderTrendData} loading={ordersSectionLoading} />
            </div>
          </div>

          {/* 最新订单列表 */}
          <TableCard<Order>
            dataSource={ordersData.slice(0, 10)}
            columns={[
              { title: '订单ID', dataIndex: 'order_id', key: 'order_id', width: 120 },
              { title: '商品名称', dataIndex: 'product_name', key: 'product_name', ellipsis: true, width: 200 },
              { title: '金额', dataIndex: 'amount', key: 'amount', align: 'right' as const, width: 120, render: formatCurrency },
              { title: '状态', dataIndex: 'status', key: 'status', align: 'center' as const, width: 100, render: (status) => {
                const s = statusMap[status] || { color: 'default', text: status };
                return <Tag color={s.color}>{s.text}</Tag>;
              }},
              { title: '下单时间', dataIndex: 'create_time', key: 'create_time', width: 180, render: formatDateTime },
            ]}
            rowKey="order_id"
            pagination={false}
            size="middle"
            loading={ordersSectionLoading}
            error={ordersError}
          />
        </div>
      </div>

      {/* 创作者数据区域 */}
      <div className={styles.sectionCard}>
        <div className={styles.sectionHeader}>
          <Title level={4} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--spacing-2)' }}>
            <TeamOutlined style={{ color: 'var(--color-warning-500)' }} />
            创作者数据
          </Title>
          <Space>
            <Button type="link" size="small" onClick={() => refetchCreators()}>刷新</Button>
          </Space>
        </div>
        
        <CreatorDataCard
          totalFollowers={totalFollowers}
          todayNewFollowers={todayNewFollowers}
          avgEngagementRate={avgEngagementRate}
          trendData={creatorTrendData}
          loading={creatorsSectionLoading}
        />
      </div>
    </PageContainer>
  );
};

export default Dashboard;
