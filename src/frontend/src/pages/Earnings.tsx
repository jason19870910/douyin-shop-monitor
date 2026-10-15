import { Card, Spin, Descriptions, Tag, Row, Col, Statistic, Divider, Alert } from 'antd';
import { useApi } from '@/hooks/useApi';
import { earningsApi, type CreatorIncomeSummary } from '@/api/index';
import { PageContainer, PageHeader } from '@/components/layout';

// 收益概览页面（/douyin/earnings）
const Earnings = () => {
  const { data: incomeSummary, isLoading } = useApi(() => earningsApi.getIncomeSummary() as Promise<CreatorIncomeSummary | undefined>, ['creator-income-summary']);

  const renderSummary = () => {
    if (isLoading) return <Spin size="large" style={{ display: 'block', margin: '24px auto' }} />;
    if (!incomeSummary) return <Alert message="无法获取收益数据" type="error" showIcon />;

    const totalCategories = incomeSummary.total_income_summary.category_list;
    const hasCategoryData = totalCategories.length > 0;

    return (
      <>
        <Row gutter={[24, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic title="今日总收益(分)" value={incomeSummary.today_total_income} precision={0} />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic title="账户余额(分)" value={incomeSummary.total_balance} precision={0} />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic title="历史总收益(分)" value={incomeSummary.total_income_summary.history_total_income || 0} precision={0} />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic title="接口状态" value={incomeSummary.status_code === 0 ? '正常' : '异常'} />
            </Card>
          </Col>
        </Row>

        <Divider>分类收益明细 (历史汇总)</Divider>

        {hasCategoryData ? (
          <Row gutter={[16, 16]}>
            {totalCategories.map((cat, idx) => (
              <Col xs={24} sm={12} lg={6} key={cat.category_id || idx}>
                <Card>
                  <Statistic
                    title={cat.name}
                    value={cat.yesterday_total_income || 0}
                    precision={0}
                    suffix="分"
                  />
                </Card>
              </Col>
            ))}
          </Row>
        ) : (
          <Alert message="暂无分类收益数据" type="info" showIcon />
        )}

        <Divider>各周期汇总</Divider>
        <Descriptions layout="horizontal" size="middle" column={4}>
          <Descriptions.Item label="Day1 收益" span={1}>
            <Tag color={incomeSummary.day1_income_summary.category_list.length > 0 ? 'green' : 'default'}>
              {incomeSummary.day1_income_summary.history_total_income || 0}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Day7 收益" span={1}>
            <Tag color={incomeSummary.day7_income_summary.category_list.length > 0 ? 'green' : 'default'}>
              {incomeSummary.day7_income_summary.history_total_income || 0}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Day30 收益" span={1}>
            <Tag color={incomeSummary.day30_income_summary.category_list.length > 0 ? 'green' : 'default'}>
              {incomeSummary.day30_income_summary.history_total_income || 0}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="数据更新状态" span={1}>
            <Tag color={incomeSummary.data_update_status === 1 ? 'green' : 'orange'}>
              {incomeSummary.data_update_status === 1 ? '正常' : '延迟'}
            </Tag>
          </Descriptions.Item>
        </Descriptions>
      </>
    );
  };

  return (
    <PageContainer>
      <PageHeader title="收益概览" subtitle="创作者收益汇总数据（抖音开放平台）" />
      {renderSummary()}
    </PageContainer>
  );
};

export default Earnings;
