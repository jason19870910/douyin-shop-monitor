import { Card, Spin, Descriptions, Tag, Row, Col, Statistic, Divider, Alert, Table } from 'antd';
import { useApi } from '@/hooks/useApi';
import { earningsApi, type CreatorIncomeDetail } from '@/api/index';
import { PageContainer, PageHeader } from '@/components/layout';

// 收益趋势页面（/douyin/earnings/trend）
const EarningsTrend = () => {
  const { data: incomeDetail, isLoading } = useApi(() => earningsApi.getIncomeDetail() as Promise<CreatorIncomeDetail | undefined>, ['creator-income-detail']);

  const renderDetail = () => {
    if (isLoading) return <Spin size="large" style={{ display: 'block', margin: '24px auto' }} />;
    if (!incomeDetail) return <Alert message="无法获取收益趋势数据" type="error" showIcon />;

    const chartPoints = incomeDetail.chart_coordinate_list || [];
    const incomeItems = incomeDetail.income_item_list || [];

    // 格式化时间戳为日期字符串
    const formatDate = (timestamp: number) => {
      const date = new Date(timestamp * 1000);
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', weekday: 'short' });
    };

    return (
      <>
        <Row gutter={[24, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic title="趋势图数据点" value={chartPoints.length} precision={0} />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic title="明细记录条数" value={incomeItems.length} precision={0} />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic title="接口状态" value={incomeDetail.status_code === 0 ? '正常' : '异常'} />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic title="总收益(分)" value={incomeItems.reduce((sum, item) => sum + (item.amount || 0), 0)} precision={0} />
            </Card>
          </Col>
        </Row>

        <Divider>每日收益明细 (近7天)</Divider>

        {incomeItems.length > 0 ? (
          <Table
            dataSource={incomeItems.map((item, idx) => ({
              key: idx,
              date: formatDate(item.timestamp || 0),
              timestamp: item.timestamp,
              amount: item.amount || 0,
              name: item.name || '—',
            }))}
            columns={[
              { title: '日期', dataIndex: 'date', width: 160 },
              { title: '时间戳', dataIndex: 'timestamp', width: 120 },
              { title: '收益(分)', dataIndex: 'amount', align: 'right', width: 120 },
              { title: '来源', dataIndex: 'name', width: 200 },
            ]}
            pagination={false}
            size="middle"
            bordered
          />
        ) : (
          <Alert message="暂无收益明细数据" type="info" showIcon />
        )}

        {chartPoints.length > 0 && (
          <>
            <Divider>趋势图坐标点</Divider>
            <Descriptions layout="horizontal" size="middle" column={4}>
              {chartPoints.slice(0, 8).map((point: unknown, idx) => {
                const p = point as { x?: number; y?: number };
                return (
                  <Descriptions.Item key={idx} label={`点 ${idx + 1}`}>
                    <Tag>({p.x}, {p.y})</Tag>
                  </Descriptions.Item>
                );
              })}
            </Descriptions>
          </>
        )}
      </>
    );
  };

  return (
    <PageContainer>
      <PageHeader title="收益趋势" subtitle="创作者收益趋势与明细数据（抖音开放平台）" />
      {renderDetail()}
    </PageContainer>
  );
};

export default EarningsTrend;
