import { useMemo, useState } from 'react';
import { Row, Col, Card, Spin, Empty, Descriptions, Tag, Badge } from 'antd';
import { DollarOutlined, ShoppingCartOutlined, TeamOutlined, FireOutlined, ShoppingOutlined } from '@ant-design/icons';
import { formatNumber, formatCurrency, formatPercent, formatDate, formatDateTime } from '@/utils/formatters';
import { useDashboardStats, useProductsStats, useCreatorsOverview, queryKeys, type ProductStatsData, type CreatorsOverviewData } from '@/hooks/useQueries';
import { colors } from '@/theme/tokens';
import { CreatorTrendData } from '@/components/dashboard/CreatorDataCard';
import { DataTable, type DataTableColumn } from '@/components/common';
import { MetricCard } from '@/components/dashboard/MetricCard';
import { CreatorDataCard } from '@/components/dashboard/CreatorDataCard';
import { OrderTrendMiniChart } from '@/components/dashboard/OrderTrendMiniChart';
import { OrderStatusDistribution } from '@/components/dashboard/OrderStatusDistribution';
import { SkeletonCard } from '@/components/dashboard/SkeletonCard';
import { dashboardApi, type Product, type Order } from '@/api/index';

const Dashboard = () => {
  const { data: dashboardStats, isLoading: dashboardStatsLoading, isError: dashboardStatsError } = useDashboardStats({});
  const productStatsResult = useProductsStats({});
  const productStats: ProductStatsData | undefined = productStatsResult.data as unknown as ProductStatsData | undefined;
  const { data: creatorsOverview, isLoading: creatorsOverviewLoading }: { data: CreatorsOverviewData | undefined; isLoading: boolean } = useCreatorsOverview({});
  const [productTab] = useState<'onSale' | 'stock' | 'violation'>('onSale');
  const metricCards = useMemo(() => [
    { label: '今日销售额', value: formatCurrency(dashboardStats?.total_revenue_today ?? 0), trend: dashboardStats?.total_revenue_yesterday ? ((dashboardStats.total_revenue_today - dashboardStats.total_revenue_yesterday) / (dashboardStats.total_revenue_yesterday || 1)) * 100 : undefined, prefix: <DollarOutlined style={{ color: colors.primary[500] }} /> },
    { label: '今日订单数', value: formatNumber(dashboardStats?.total_orders_today ?? 0), trend: dashboardStats?.total_orders_yesterday ? ((dashboardStats.total_orders_today - dashboardStats.total_orders_yesterday) / (dashboardStats.total_orders_yesterday || 1)) * 100 : undefined, prefix: <ShoppingCartOutlined style={{ color: colors.success[500] }} /> },
    { label: '今日销量', value: formatNumber(dashboardStats?.total_sales_today ?? 0), trend: dashboardStats?.total_sales_yesterday ? ((dashboardStats.total_sales_today - dashboardStats.total_sales_yesterday) / (dashboardStats.total_sales_yesterday || 1)) * 100 : undefined, prefix: <FireOutlined style={{ color: colors.warning[500] }} /> },
    { label: '转化率', value: formatPercent(dashboardStats?.avg_conversion_rate ?? 0), trend: dashboardStats?.avg_conversion_rate_yesterday ? ((dashboardStats.avg_conversion_rate - dashboardStats.avg_conversion_rate_yesterday) / (dashboardStats.avg_conversion_rate_yesterday || 1)) * 100 : undefined, prefix: <ShoppingOutlined style={{ color: colors.info[500] }} /> },
    { label: '商品总数', value: formatNumber(dashboardStats?.products?.total ?? (productStats?.[productTab] as { total_count?: number } | undefined)?.total_count ?? 0), prefix: <ShoppingOutlined style={{ color: colors.accent.blue }} /> },
    { label: '创作者粉丝', value: formatNumber(dashboardStats?.creators?.total_followers ?? 0), trend: creatorsOverview?.today_new_followers ?? undefined, prefix: <TeamOutlined style={{ color: colors.brand.purple }} /> },
  ], [dashboardStats, productStats, productTab, creatorsOverview]);

  const hotProductColumns = useMemo<DataTableColumn<Product>[]>(() => [
    { title: '排名', dataIndex: 'rank', key: 'rank', width: 70, align: 'center', render: (_: unknown, _record: Product, index: number) => index + 1 },
    { title: '商品ID', dataIndex: 'product_id', key: 'product_id', width: 120 },
    { title: '商品名称', dataIndex: 'product_name', key: 'product_name', width: 240, ellipsis: true },
    { title: '价格', dataIndex: 'price_lower', key: 'price', width: 100, align: 'right', render: (_v: unknown, record: Product) => formatCurrency(((record.price_lower ?? record.price_higher ?? record.market_price ?? 0) as number) / 100) },
    { title: '今日销量', dataIndex: 'sales_today', key: 'sales_today', width: 100, align: 'right', render: (v: unknown) => formatNumber(v as number) },
    { title: '昨日销量', dataIndex: 'sales_yesterday', key: 'sales_yesterday', width: 100, align: 'right', render: (v: unknown) => formatNumber(v as number) },
    { title: '库存', dataIndex: 'inventory', key: 'inventory', width: 80, align: 'right', render: (v: unknown) => { const num = v as number; return <span style={{ color: num <= 10 ? 'var(--color-error-500)' : 'var(--color-text-secondary)', fontWeight: num <= 10 ? 600 : 400 }}>{formatNumber(num)}{num <= 10 && <Tag color="red" style={{ marginLeft: 8, fontSize: 10 }}>低库存</Tag>}</span>; }},
    { title: '转化率', dataIndex: 'conversion_rate', key: 'conversion_rate', width: 100, align: 'right', render: (v: unknown) => formatPercent(v as number) },
    { title: '更新时间', dataIndex: 'fetched_at', key: 'fetched_at', width: 160, render: (v: unknown) => formatDate(v as string | null | undefined) },
  ], []);

  const latestOrderColumns = useMemo<DataTableColumn<Order>[]>(() => [
    { title: '订单ID', dataIndex: 'order_id', key: 'order_id', width: 150 },
    { title: '商品名称', dataIndex: 'product_name', key: 'product_name', width: 200, ellipsis: true },
    { title: '金额', dataIndex: 'pay_amount', key: 'amount', width: 120, align: 'right', render: (_v: unknown, record: Order) => formatCurrency((record.pay_amount ?? record.total_price ?? 0) as number) },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, align: 'center', render: (status: unknown) => { const statusStr = typeof status === 'string' ? status : ''; const colors: Record<string, string> = { completed: 'green', pending: 'orange', shipped: 'blue', cancelled: 'red', refunded: 'purple' }; const labels: Record<string, string> = { completed: '已完成', pending: '待处理', shipped: '已发货', cancelled: '已取消', refunded: '已退款' }; return <Tag color={colors[statusStr] || 'default'}>{labels[statusStr] || statusStr}</Tag>; }},
    { title: '下单时间', dataIndex: 'create_time', key: 'create_time', width: 180, render: (v: unknown) => formatDate(v as string | null | undefined) },
  ], []);

  // 使用后端返回的真实订单状态分布数据
  const orderStatusData = useMemo(() => {
    if (!dashboardStats?.order_status_distribution) return [];
    return Object.entries(dashboardStats.order_status_distribution).map(([status, data]: [string, { count: number; amount: number }]) => ({
      status,
      count: data.count,
      amount: data.amount,
    }));
  }, [dashboardStats]);

  // 使用后端返回的最近订单数据
  const recentOrdersData = useMemo(() => {
    if (!dashboardStats?.recent_orders) return [];
    return dashboardStats.recent_orders as Order[];
  }, [dashboardStats]);

  if (dashboardStatsLoading) {
    return (
      <Spin size="large" tip="加载仪表盘数据...">
        <Row gutter={[16, 16]}>
          {metricCards.map((_, i) => (
            <Col key={i} xs={24} sm={12} lg={8} xl={6}><SkeletonCard variant="metric" /></Col>
          ))}
          <Col xs={24} lg={12}><SkeletonCard variant="chart" /></Col>
          <Col xs={24} lg={12}><SkeletonCard variant="chart" /></Col>
          <Col xs={24} lg={12}><SkeletonCard variant="chart" /></Col>
          <Col xs={24} lg={12}><SkeletonCard variant="table" /></Col>
          <Col xs={24}><SkeletonCard variant="table" /></Col>
        </Row>
      </Spin>
    );
  }

  if (dashboardStatsError) {
    return (
      <Card style={{ marginTop: 24 }}>
        <Empty description="加载仪表盘数据失败" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </Card>
    );
  }

  return (
    <div style={{ padding: '0 24px 24px' }}>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {metricCards.map((card, index) => (
          <Col key={index} xs={24} sm={12} lg={8} xl={6}>
            <MetricCard {...card} />
          </Col>
        ))}
      </Row>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="销售趋势 (近7天)" loading={dashboardStatsLoading}>
            <OrderTrendMiniChart data={Array.isArray(dashboardStats?.sales_trend) ? dashboardStats.sales_trend : []} title="销售额趋势" color="var(--color-primary-500)" loading={dashboardStatsLoading} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="收入趋势 (近7天)" loading={dashboardStatsLoading}>
            <OrderTrendMiniChart data={Array.isArray(dashboardStats?.revenue_trend) ? dashboardStats.revenue_trend : []} title="收入趋势" color="var(--color-success-500)" loading={dashboardStatsLoading} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="热销商品 TOP 10" loading={dashboardStatsLoading}>
            {dashboardStatsError ? <Empty description="加载失败" /> : dashboardStats?.top_products && dashboardStats.top_products.length > 0 ? (
              <DataTable<Product> title="热销商品 TOP 10" queryKey={queryKeys.dashboard.stats({})} queryFn={(params) => dashboardApi.getStats(params).then(res => ({ items: res?.top_products || [], total: res?.top_products?.length || 0 })) as Promise<{ items: Product[]; total: number }>} columns={hotProductColumns} rowKey="product_id" defaultPageSize={10} exportConfig={{ filenamePrefix: 'dashboard_hot_products', columns: [{ key: 'rank', label: '排名' }, { key: 'product_id', label: '商品ID' }, { key: 'product_name', label: '商品名称' }, { key: 'price_lower', label: '价格', render: (record: Product) => ((record.price_lower ?? record.price_higher ?? record.market_price ?? 0) as number) / 100 }, { key: 'sales_today', label: '今日销量' }, { key: 'sales_yesterday', label: '昨日销量' }, { key: 'inventory', label: '库存' }, { key: 'conversion_rate', label: '转化率' }, { key: 'fetched_at', label: '更新时间' }] }} />
            ) : <Empty description="暂无热销商品数据" />}
          </Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="订单状态分布" loading={dashboardStatsLoading}>
            {/* @ts-ignore - orderStatusData 类型为 OrderStatusItem[], 组件接收兼容类型 */}
            <OrderStatusDistribution data={orderStatusData} loading={dashboardStatsLoading} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="订单趋势 (近7天)" loading={dashboardStatsLoading}>
            <OrderTrendMiniChart data={Array.isArray(dashboardStats?.order_trend) ? dashboardStats.order_trend : []} title="订单量趋势" color="var(--color-warning-500)" loading={dashboardStatsLoading} />
          </Card>
        </Col>
        <Col xs={24}>
          <Card title="最新订单 (TOP 10)" loading={dashboardStatsLoading}>
            {dashboardStatsError ? <Empty description="加载失败" /> : recentOrdersData.length > 0 ? (
              <DataTable<Order> title="最新订单 (TOP 10)" queryKey={queryKeys.orders.list({})} queryFn={() => Promise.resolve({ items: recentOrdersData, total: recentOrdersData.length })} columns={latestOrderColumns} rowKey="order_id" defaultPageSize={10} />
            ) : <Empty description="暂无订单数据" />}
          </Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24}>
          <Card title="创作者数据概览" loading={creatorsOverviewLoading}>
            {creatorsOverview ? (
              <CreatorDataCard totalFollowers={creatorsOverview.total_followers ?? 0} todayNewFollowers={creatorsOverview.today_new_followers ?? 0} avgEngagementRate={creatorsOverview.avg_engagement_rate ?? 0} trendData={(creatorsOverview.trend_data ?? []) as CreatorTrendData[]} loading={creatorsOverviewLoading} />
            ) : <Empty description="暂无创作者数据" />}
          </Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card title="数据源状态">
            <Descriptions column={4} size="small" bordered layout="vertical">
              <Descriptions.Item label="数据源">
                <Badge status={dashboardStats?.data_source === 'real' ? 'success' : dashboardStats?.data_source === 'mock' ? 'warning' : 'processing'} text={dashboardStats?.data_source === 'real' ? '真实数据' : dashboardStats?.data_source === 'mock' ? '模拟数据' : '缓存数据'} />
              </Descriptions.Item>
              <Descriptions.Item label="商品数据">
                <span>总计 {formatNumber(dashboardStats?.products?.total ?? 0)} | 在售 {formatNumber(dashboardStats?.products?.on_sale ?? 0)}</span>
              </Descriptions.Item>
              <Descriptions.Item label="订单数据">
                <span>总计 {formatNumber(dashboardStats?.orders?.total ?? 0)} | 金额 {formatCurrency(dashboardStats?.orders?.total_amount ?? 0)}</span>
              </Descriptions.Item>
              <Descriptions.Item label="创作者数据">
                <span>总计 {formatNumber(dashboardStats?.creators?.total ?? 0)} | 粉丝 {formatNumber(dashboardStats?.creators?.total_followers ?? 0)}</span>
              </Descriptions.Item>
              <Descriptions.Item label="视频数据">
                <span>总计 {formatNumber(dashboardStats?.videos?.total ?? 0)} | 播放 {formatNumber(dashboardStats?.videos?.total_views ?? 0)}</span>
              </Descriptions.Item>
              <Descriptions.Item label="健康检查时间">
                <span>{dashboardStats?.timestamp ? formatDateTime(dashboardStats.timestamp) : '暂无'}</span>
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;