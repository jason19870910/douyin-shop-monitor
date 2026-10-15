import { useState, type ReactNode } from 'react';
import { Row, Col, Card, Statistic, Spin, Button, Tabs, Empty, Tag, message, Descriptions } from 'antd';
import { SyncOutlined, ShoppingOutlined, DollarOutlined, ShoppingCartOutlined, TeamOutlined } from '@ant-design/icons';
// 使用独立统计端点替代聚合的 dashboard/stats，避免缓存不一致
// 趋势和 TOP 数据仍使用 dashboard/stats 端点
import { useHealthCheck, useProductsStats, useOrdersStats, useCreatorsOverview, useManualSync, useExternalApiHealth, useDashboardStats, queryKeys, type OrderStatsData } from '@/hooks/useQueries';
import { useQueryClient } from '@tanstack/react-query';
import { PageContainer, PageHeader } from '@/components/layout';
import { formatNumber, formatCurrency, formatPercent } from '@/utils/formatters';
import { OrderTrendMiniChart } from '@/components/dashboard/OrderTrendMiniChart';
import OrderStatusDistribution from '@/components/dashboard/OrderStatusDistribution';
import { DataTable } from '@/components/common';
import { dashboardApi, type Product } from '@/api/index';
import { colors } from '@/theme/tokens';

interface OrderStatusItem {
  status: string;
  count: number;
  amount: number;
}

const transformOrderStatsToStatusData = (stats: OrderStatsData): OrderStatusItem[] => {
  const result: OrderStatusItem[] = [];

  // Add "all" order
  const all = stats.all as { count?: number; amount?: number } | undefined;
  if (all && typeof all === 'object') {
    const count = all.count !== undefined ? all.count : 0;
    result.push({
      status: 'all',
      count,
      amount: typeof all.amount === 'number' ? all.amount : 0,
    });
  }

  // Add "pay" order
  const pay = stats.pay as { count?: number; amount?: number } | undefined;
  if (pay && typeof pay === 'object') {
    const count = pay.count !== undefined ? pay.count : 0;
    result.push({
      status: 'pay',
      count,
      amount: typeof pay.amount === 'number' ? pay.amount : 0,
    });
  }

  // Add "cancel" order
  const cancel = stats.cancel as { count?: number; amount?: number } | undefined;
  if (cancel && typeof cancel === 'object') {
    const count = cancel.count !== undefined ? cancel.count : 0;
    result.push({
      status: 'cancel',
      count,
      amount: typeof cancel.amount === 'number' ? cancel.amount : 0,
    });
  }

  // Add sub-tab orders from sub_tab_count_map
  const subTabMap = stats.sub_tab_count_map as Record<string, { count?: number; amount?: number }> | undefined;
  if (subTabMap && typeof subTabMap === 'object') {
    Object.entries(subTabMap).forEach(([key, val]) => {
      if (val && typeof val === 'object') {
        const count = val.count !== undefined ? val.count : 0;
        result.push({
          status: key,
          count,
          amount: typeof val.amount === 'number' ? val.amount : 0,
        });
      }
    });
  }

  return result.length > 0 ? result : [{ status: 'none', count: 0, amount: 0 }];
};

const { TabPane } = Tabs;

const Home = () => {
  const [productTab, setProductTab] = useState('onSale');
  const queryClient = useQueryClient();

  const { data: health } = useHealthCheck({});
  const { data: externalHealth, isLoading: externalHealthLoading } = useExternalApiHealth({});
  
  // 使用独立统计端点，实时调用外部 API，避免缓存不一致
  const { data: productStats, isLoading: productStatsLoading, isError: productStatsError } = useProductsStats({});
  const { data: orderStats, isLoading: orderStatsLoading, isError: orderStatsError } = useOrdersStats({});
  const { data: creatorOverview, isLoading: creatorOverviewLoading, isError: creatorOverviewError } = useCreatorsOverview({ recent_days: 7 });

  // 趋势和 TOP 数据使用聚合端点
  const { data: dashboardStats, isLoading: dashboardStatsLoading, isError: dashboardStatsError } = useDashboardStats({});

  const manualSyncMutation = useManualSync({
    onSuccess: () => {
      message.success('同步已触发');
      queryClient.invalidateQueries({ queryKey: queryKeys.health.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.products.stats() });
      queryClient.invalidateQueries({ queryKey: queryKeys.orders.stats() });
      queryClient.invalidateQueries({ queryKey: queryKeys.creators.overview({ recent_days: 7 }) });
    },
    onError: () => {
      message.error('同步失败');
    },
  });

  const handleSync = () => {
    manualSyncMutation.mutate(false); // 同步模式
  };

  // 核心 KPI 指标卡片 - 从独立端点聚合
  // API 返回结构: {total, onsale, stock, violation} 需断言为 Record<string, unknown>
  const productStatsData = productStats as Record<string, unknown> | undefined;
  const orderStatsData = orderStats as Record<string, unknown> | undefined;
  const creatorOverviewData = creatorOverview as Record<string, unknown> | undefined;

  const totalProducts = (productStatsData?.total as number) ?? 0;
  const onSaleProducts = (productStatsData?.onsale as number) ?? 0;
  const totalOrders = (orderStatsData?.all as { count?: number } | undefined)?.count ?? 0;
  const totalAmount = (orderStatsData?.all as { amount?: number } | undefined)?.amount ?? 0;
  const totalFollowers = (creatorOverviewData?.total_followers as number) ?? 0;
  const totalVideos = (creatorOverviewData?.total_videos as number) ?? 0;
  const totalViews = (creatorOverviewData?.total_views as number) ?? 0;
  const totalCreators = (creatorOverviewData?.total as number) ?? 0;
  const avgConversion = totalOrders > 0 && totalAmount > 0 ? 0 : 0; // 独立端点暂无转化率，后续可扩展

  const isLoading = productStatsLoading || orderStatsLoading || creatorOverviewLoading;

  return (
    <PageContainer>
      <PageHeader title="抖音电商数据监控平台" subtitle="实时数据概览" />
      
      {/* 核心 KPI 指标卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={isLoading}>
            <Statistic
              title="今日销售额"
              value={formatNumber(totalAmount)}
              suffix={`元 | 客单价 ${formatCurrency(totalOrders > 0 ? totalAmount / totalOrders : 0).replace('¥', '')}元`}
              prefix={<DollarOutlined style={{ color: colors.primary[500] }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={isLoading}>
            <Statistic
              title="今日订单数"
              value={formatNumber(totalOrders)}
              suffix={`笔 | 转化率 ${formatPercent(avgConversion)}`}
              prefix={<ShoppingCartOutlined style={{ color: colors.success[500] }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={isLoading}>
            <Statistic
              title="商品概览"
              value={formatNumber(totalProducts)}
              suffix={`总数 | 在售 ${onSaleProducts}`}
              prefix={<ShoppingOutlined style={{ color: colors.brand.purple }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={isLoading}>
            <Statistic
              title="创作者与视频"
              value={formatNumber(totalCreators)}
              suffix={`达人 | 粉丝 ${formatNumber(totalFollowers)} | 视频 ${totalVideos} | 播放 ${formatNumber(totalViews)}`}
              prefix={<TeamOutlined style={{ color: colors.warning[500] }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 销售趋势图表 & 热销商品 (独立端点暂无趋势/TOP数据，显示占位) */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <div style={{ borderLeft: '4px solid var(--color-primary-500)', paddingLeft: 12 }}>
            <Card title="销售趋势 (近7天)" loading={dashboardStatsLoading}>
              <OrderTrendMiniChart
                data={Array.isArray(dashboardStats?.sales_trend) ? dashboardStats.sales_trend : []}
                title="销售额趋势"
                color="var(--color-primary-500)"
                loading={dashboardStatsLoading}
              />
            </Card>
          </div>
        </Col>
        <Col xs={24} lg={12}>
          <div style={{ borderLeft: '4px solid var(--color-warning-500)', paddingLeft: 12 }}>
            <Card title="热销商品 TOP 5" loading={dashboardStatsLoading}>
              {dashboardStatsError ? (
                <Empty description="加载失败" />
              ) : dashboardStats?.top_products && dashboardStats.top_products.length > 0 ? (
                <DataTable<Product>
                  title="热销商品 TOP 5"
                  queryKey={queryKeys.dashboard.stats({})}
                  queryFn={(params) => dashboardApi.getStats(params).then(res => ({ items: res?.top_products || [], total: res?.top_products?.length || 0 })) as Promise<{ items: Product[]; total: number }>}
                  columns={[
                    { title: '排名', dataIndex: 'rank', key: 'rank', width: 70, align: 'center', render: (_: unknown, _record: Product, index: number) => index + 1 },
                    { title: '商品名称', dataIndex: 'product_name', key: 'product_name', width: 200, ellipsis: true },
                    { title: '价格', dataIndex: 'price_lower', key: 'price', width: 100, align: 'right', render: (_v: unknown, record: Product) => formatCurrency(((record.price_lower ?? record.price_higher ?? record.market_price ?? 0) as number) / 100) },
                    { title: '今日销量', dataIndex: 'sales_today', key: 'sales_today', width: 100, align: 'right', render: (v: unknown) => formatNumber(v as number) },
                  ]}
                  rowKey="product_id"
                  defaultPageSize={5}
                />
              ) : (
                <Empty description="暂无热销商品数据" />
              )}
            </Card>
          </div>
        </Col>
      </Row>

      {/* 商品统计详情 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <div style={{ borderLeft: '4px solid var(--color-primary-500)', paddingLeft: 12 }}>
            <Card title="商品统计详情" loading={productStatsLoading}>
              <Tabs activeKey={productTab} onChange={setProductTab}>
                {['onSale', 'stock', 'violation'].map(k => (
                  <TabPane tab={k === 'onSale' ? '在售' : k === 'stock' ? '库存' : '违规'} key={k}>
                    <Spin spinning={productStatsLoading}>
                      {productStatsError ? (
                        <Empty description="加载失败" />
                      ) : productStats ? (
                        renderProductStats(productStats)
                      ) : (
                        <Empty description="暂无数据" />
                      )}
                    </Spin>
                  </TabPane>
                ))}
              </Tabs>
            </Card>
          </div>
        </Col>
      </Row>

      {/* 订单统计详情 & 订单状态分布 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <div style={{ borderLeft: '4px solid var(--color-success-500)', paddingLeft: 12 }}>
            <Card title="订单统计详情" loading={orderStatsLoading}>
              <Spin spinning={orderStatsLoading}>
                {orderStatsError ? (
                  <Empty description="加载失败" />
                ) : orderStats ? (
                  <Descriptions column={4} size="small" bordered>
                    {Object.entries(orderStats || {})
                      .map(([key, val]: [string, any]) => {
                        const label = key === 'all' ? '全部' : key === 'pay' ? '支付' : key === 'cancel' ? '取消' : key === 'unpaid' ? '待付款' : key === 'handling' ? '处理中' : key === 'wait_send' ? '待发货' : key === 'wait_pay' ? '待支付' : key === 'on_delivery' ? '配送中' : key === 'received' ? '已收货' : key === 'closed' ? '已关闭' : key;
                        if (val && typeof val === 'object') {
                          return (
                            <Descriptions.Item key={key} label={label} span={2}>
                              <div><strong>数量:</strong> {val.count ?? 0}</div>
                              <div><strong>金额:</strong> {val.amount ?? 0}元</div>
                            </Descriptions.Item>
                          );
                        }
                        return (
                          <Descriptions.Item key={key} label={label}>
                            <div><strong>数量:</strong> {val ?? 0}</div>
                          </Descriptions.Item>
                        );
                      })}
                  </Descriptions>
                ) : (
                  <Empty description="暂无数据" />
                )}
              </Spin>
            </Card>
          </div>
        </Col>
      <Col xs={24} lg={12}>
        <div style={{ borderLeft: '4px solid var(--color-primary-500)', paddingLeft: 12 }}>
          <Card title="订单状态分布" loading={orderStatsLoading}>
            {orderStatsError ? (
              <Empty description="加载失败" />
            ) : orderStats ? (
              <OrderStatusDistribution
                // @ts-ignore - TypeScript 类型推断冲突，运行时类型正确
                data={transformOrderStatsToStatusData(orderStats)}
                loading={orderStatsLoading}
              />
            ) : (
              <Empty description="暂无数据" />
            )}
          </Card>
        </div>
      </Col>
      </Row>

      {/* 创作者中心概览 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <div style={{ borderLeft: '4px solid var(--color-success-500)', paddingLeft: 12 }}>
            <Card title="创作者中心概览" loading={creatorOverviewLoading}>
              <Spin spinning={creatorOverviewLoading}>
                {creatorOverviewError ? (
                  <Empty description="加载失败" />
                ) : creatorOverview ? (
                  <Descriptions column={4} size="small" bordered>
                    {/* 基础概览 */}
                    <Descriptions.Item label="总粉丝数" span={1}>{formatNumber((creatorOverview?.total_followers as number) ?? 0)}</Descriptions.Item>
                    <Descriptions.Item label="近期投稿" span={1}>{formatNumber((creatorOverview?.total_videos as number) ?? 0)}</Descriptions.Item>
                    <Descriptions.Item label="近期播放" span={1}>{formatNumber((creatorOverview?.recent_view as number) ?? 0)}</Descriptions.Item>
                    <Descriptions.Item label="近期点赞" span={1}>{formatNumber((creatorOverview?.recent_like as number) ?? 0)}</Descriptions.Item>
                    
                    {/* 互动详情 */}
                    <Descriptions.Item label="近期分享" span={1}>{formatNumber((creatorOverview?.recent_share as number) ?? 0)}</Descriptions.Item>
                    <Descriptions.Item label="近期评论" span={1}>{formatNumber((creatorOverview?.recent_comment as number) ?? 0)}</Descriptions.Item>
                    <Descriptions.Item label="主页访问" span={1}>{formatNumber((creatorOverview?.recent_homepage_view as number) ?? 0)}</Descriptions.Item>
                    <Descriptions.Item label="封面点击率" span={1}>
                      {((creatorOverview?.cover_click_ratio as number) ?? 0).toFixed(2)}%
                    </Descriptions.Item>
                    
                    {/* 粉丝变化 */}
                    <Descriptions.Item label="净增粉丝" span={1}>
                      {(creatorOverview?.net_followers_gain as number) ?? 0}
                    </Descriptions.Item>
                    <Descriptions.Item label="取关粉丝" span={1}>
                      {formatNumber((creatorOverview?.cancel_followers as number) ?? 0)}
                    </Descriptions.Item>
                    
                    {/* 视频质量指标 */}
                    <Descriptions.Item label="5秒完播率" span={1}>
                      {(((creatorOverview?.completion_rate_5s as number) ?? 0) * 100).toFixed(1)}%
                    </Descriptions.Item>
                    <Descriptions.Item label="2秒跳出率" span={1}>
                      {(((creatorOverview?.bounce_rate_2s as number) ?? 0) * 100).toFixed(1)}%
                    </Descriptions.Item>
                    <Descriptions.Item label="平均播放时长" span={1}>
                      {(creatorOverview?.avg_view_second as number) ?? 0}s
                    </Descriptions.Item>
                    
                    {/* 兼容字段（近期7天汇总） */}
                    <Descriptions.Item label="近期总播放" span={1}>{formatNumber((creatorOverview?.total_views as number) ?? 0)}</Descriptions.Item>
                    <Descriptions.Item label="近期总点赞" span={1}>{formatNumber((creatorOverview?.total_likes as number) ?? 0)}</Descriptions.Item>
                    <Descriptions.Item label="近期总评论" span={1}>{formatNumber((creatorOverview?.total_comments as number) ?? 0)}</Descriptions.Item>
                    <Descriptions.Item label="近期总分享" span={1}>{formatNumber((creatorOverview?.total_shares as number) ?? 0)}</Descriptions.Item>
                    
                    {/* 元数据 */}
                    <Descriptions.Item label="数据来源" span={1}>{creatorOverview?.data_source ?? '-'}</Descriptions.Item>
                    <Descriptions.Item label="统计天数" span={1}>{creatorOverview?.recent_days ?? 7}天</Descriptions.Item>
                  </Descriptions>
                ) : (
                  <Empty description="暂无数据" />
                )}
              </Spin>
            </Card>
          </div>
        </Col>
      </Row>

      {/* 系统健康 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <div style={{ borderLeft: '4px solid var(--color-warning-500)', paddingLeft: 12 }}>
            <Card title="系统健康">
              <Row gutter={16}>
                <Col xs={24} sm={6}>
                  <Statistic
                    title="系统状态"
                    value={health?.status ?? '未知'}
                    prefix={
                      <Tag color={health?.status === 'healthy' ? 'green' : 'orange'}>
                        {health?.status === 'healthy' ? '正常' : '异常'}
                      </Tag>
                    }
                  />
                </Col>
                <Col xs={24} sm={6}>
                  <Statistic title="最后更新" value={health?.last_update ?? '-'} />
                </Col>
                <Col xs={24} sm={6}>
                  <Statistic title="时间戳" value={health?.timestamp ?? '-'} />
                </Col>
                <Col xs={24} sm={6}>
                  <Statistic title="数据来源" value="monitor" />
                </Col>
              </Row>
              
              {/* 外部 API 状态 */}
              <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--color-border-light)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <h4 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>外部 API 接口状态</h4>
                  {externalHealth && (
                    <Tag color={externalHealth.overall_status === 'healthy' ? 'green' : externalHealth.overall_status === 'degraded' ? 'orange' : 'red'}>
                      {externalHealth.overall_status === 'healthy' ? '全部正常' : externalHealth.overall_status === 'degraded' ? '部分异常' : '全部异常'}
                      ({externalHealth.healthy_count}/{externalHealth.total_count})
                    </Tag>
                  )}
                  {externalHealthLoading && !externalHealth && <Spin size="small" />}
                </div>
                {externalHealth && externalHealth.endpoints.length > 0 && (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                      <thead>
                        <tr style={{ background: 'var(--bg-secondary)', textAlign: 'left' }}>
                          <th style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-border-light)' }}>接口名称</th>
                          <th style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-border-light)' }}>状态</th>
                          <th style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-border-light)' }}>响应时间</th>
                          <th style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-border-light)' }}>HTTP 状态码</th>
                          <th style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-border-light)' }}>错误信息</th>
                        </tr>
                      </thead>
                      <tbody>
                        {externalHealth.endpoints.map((endpoint, index) => (
                          <tr key={index} style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                            <td style={{ padding: '8px 12px', fontWeight: 500 }}>{endpoint.name}</td>
                            <td style={{ padding: '8px 12px' }}>
                              <Tag color={
                                endpoint.status === 'healthy' ? 'green' :
                                endpoint.status === 'unhealthy' ? 'red' :
                                endpoint.status === 'timeout' ? 'orange' : 'red'
                              }>
                                {endpoint.status === 'healthy' ? '正常' :
                                 endpoint.status === 'unhealthy' ? '异常' :
                                 endpoint.status === 'timeout' ? '超时' :
                                 endpoint.status === 'connection_error' ? '连接失败' : '错误'}
                              </Tag>
                            </td>
                            <td style={{ padding: '8px 12px', color: endpoint.response_time_ms && endpoint.response_time_ms > 5000 ? 'red' : 'inherit' }}>
                              {endpoint.response_time_ms ? `${endpoint.response_time_ms}ms` : '-'}
                            </td>
                            <td style={{ padding: '8px 12px' }}>
                              {endpoint.status_code ? endpoint.status_code : '-'}
                            </td>
                            <td style={{ padding: '8px 12px', color: 'var(--color-text-tertiary)', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {endpoint.error ?? '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                {externalHealth && externalHealth.endpoints.length === 0 && (
                  <Empty description="无外部 API 配置" style={{ padding: 16 }} />
                )}
                {externalHealthLoading && !externalHealth && (
                  <Spin size="small" />
                )}
              </div>
              
              <Button type="primary" icon={<SyncOutlined />} onClick={handleSync} style={{ marginTop: 12 }}>
                立即同步
              </Button>
            </Card>
          </div>
        </Col>
      </Row>
    </PageContainer>
  );
};

interface ProductStatsItem {
  label: string;
  value: string | number;
}

const productStatsLabels: Record<string, string> = {
  total_count: '总数',
  on_sale_count: '在售数',
  stock_count: '库存预警数',
  violation_count: '违规数',
};

const formatProductStatsValue = (val: unknown): string => {
  if (val === undefined || val === null) return '0';
  if (typeof val === 'number') return String(val);
  if (typeof val === 'string') {
    const num = Number(val);
    return isNaN(num) ? val : String(Math.round(num));
  }
  return String(val);
};

const renderProductStats = (productStats: Record<string, unknown> | undefined): ReactNode => {
  if (!productStats) {
    return <Empty description="暂无数据" />;
  }

  const entries: ProductStatsItem[] = Object.entries(productStats).map(([key, val]) => ({
    label: productStatsLabels[key] || key,
    value: formatProductStatsValue(val),
  }));

  return (
    <Descriptions column={4} size="small" bordered>
      {entries.map((item, index) => (
        <Descriptions.Item key={index} label={item.label}>
          {item.value}
        </Descriptions.Item>
      ))}
    </Descriptions>
  );
};

export default Home;