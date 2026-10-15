import { Card, Spin, Descriptions, Tag, Row, Col, Statistic, Divider, Alert } from 'antd';
import { useApi } from '@/hooks/useApi';
import { compassApi, type CompassCoreIndex, type CompassIndexItem, type CompassIndexValue } from '@/api/index';
import { PageContainer, PageHeader } from '@/components/layout';

// Compass 经营概况页面（/dian/compass）
const Compass = () => {
  const { data: coreIndex, isLoading } = useApi(() => compassApi.getCoreIndex() as Promise<CompassCoreIndex | undefined>, ['compass-core-index']);

  const renderCoreIndex = () => {
    if (isLoading) return <Spin size="large" style={{ display: 'block', margin: '24px auto' }} />;
    if (!coreIndex) return <Alert message="无法获取经营概况数据" type="error" showIcon />;

    // 检查是否有错误码
    if (coreIndex.code && coreIndex.code !== '0' && coreIndex.code !== '200') {
      return (
        <Alert
          message={coreIndex.msg || '获取经营概况失败'}
          description={`错误码: ${coreIndex.code}`}
          type="error"
          showIcon
        />
      );
    }

    const data = coreIndex.data?.module_data?.homepage_core_index?.compass_general_multi_index_card_value;
    if (!data) {
      return <Alert message="暂无经营指标数据" type="info" showIcon />;
    }

    const meta = data.basic_meta;
    const values = data.data?.[0];

    if (!meta || !values) {
      return <Alert message="数据结构异常，无法解析经营指标" type="warning" showIcon />;
    }

    return (
      <>
        <Row gutter={[16, 16]}>
          {meta.map((item: CompassIndexItem, idx) => {
            const key = item.index_name;
            const val = values?.[key] as { index_value?: { value?: CompassIndexValue } } | undefined;
            const displayValue = val?.index_value?.value !== undefined ? `${val.index_value.value}` : 'N/A';
            const unit = val?.index_value?.value?.unit || '';

            return (
              <Col xs={24} sm={12} lg={6} key={key || idx}>
                <Card>
                  <Statistic title={key} value={displayValue} suffix={unit} precision={0} />
                </Card>
              </Col>
            );
          })}
        </Row>

        <Divider>原始数据结构</Divider>
        <Descriptions layout="horizontal" size="small" column={4}>
          <Descriptions.Item label="指标总数"><Tag>{meta.length}</Tag></Descriptions.Item>
          <Descriptions.Item label="数据层级"><Tag>compass_general_multi_index_card_value</Tag></Descriptions.Item>
        </Descriptions>
      </>
    );
  };

  return (
    <PageContainer>
      <PageHeader title="经营概况" subtitle="抖店 Compass 核心经营指标" />
      {renderCoreIndex()}
    </PageContainer>
  );
};

export default Compass;
