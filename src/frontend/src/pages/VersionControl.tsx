import { useState, useEffect } from 'react';
import { Row, Col, Card, Spin, Descriptions, Tag, Badge, Tabs, Empty, Statistic, Divider, Tooltip } from 'antd';
import { formatDate, formatDateTime } from '@/utils/formatters';
import { useApi } from '@/hooks/useApi';
import { PageContainer, PageHeader } from '@/components/layout';
import {
  versionApi,
  type VersionInfo,
  type ChangeRecord,
  type DeploymentStatus,
  type EnvConfig,
} from '@/api/index';

// 版本控制 tab 类型
interface TabItem { key: string; label: string }
const VERSION_CONTROL_TABS: TabItem[] = [
  { key: 'current', label: '当前版本' },
  { key: 'changes', label: '最近变更' },
  { key: 'deploy', label: '部署状态' },
  { key: 'env', label: '环境配置' },
];
type VersionControlTab = typeof VERSION_CONTROL_TABS[number]['key'];

// VersionControl 组件
const VersionControl = () => {
  const [activeTab, setActiveTab] = useState<VersionControlTab>('current');
  const [serverTime, setServerTime] = useState<string>('');

  // 实时更新服务器时间 (CST)
  useEffect(() => {
    const updateTime = () => {
      setServerTime(new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', hour12: false }));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  // 内部 API 数据（apiClient baseURL 为 /api/v1，自动携带 X-API-Key）
  const { data: versionInfo, isLoading: loadingVersion } = useApi(() => versionApi.getVersion() as Promise<VersionInfo | undefined>, ['version']);
  const { data: recentChanges, isLoading: loadingChanges } = useApi(() => versionApi.getChanges() as Promise<ChangeRecord[] | undefined>, ['changes']);
  const { data: deployStatus, isLoading: loadingDeploy } = useApi(() => versionApi.getStatus() as Promise<DeploymentStatus | undefined>, ['status']);
  const { data: envConfig, isLoading: loadingEnv } = useApi(() => versionApi.getEnv() as Promise<EnvConfig | undefined>, ['env']);

  const renderVersionInfo = () => {
    if (loadingVersion) return <Spin size="large" style={{ display: 'block', margin: '24px auto' }} />;
    if (!versionInfo) return <Empty description="获取版本信息失败" style={{ padding: 24 }} />;

    return (
      <Card>
        <Row gutter={16}>
          <Col xs={24} md={12}>
            <Statistic
              title="版本号"
              value={versionInfo.version}
              prefix={<Tag color="info">VERSION</Tag>}
              valueStyle={{ fontSize: 20, fontWeight: 600 }}
            />
          </Col>
          <Col xs={24} md={12}>
            <Statistic
              title="Git Commit"
              value={versionInfo.commit.substring(0, 12)}
              prefix={<Tag color="blue">COMMIT</Tag>}
              valueStyle={{ fontFamily: 'monospace', fontSize: 14 }}
            />
          </Col>
          <Col xs={24} md={12}>
            <Statistic
              title="构建时间"
              value={formatDateTime(versionInfo.builtAt)}
              prefix={<Tag color="purple">BUILT</Tag>}
            />
          </Col>
          <Col xs={24} md={12}>
            <Statistic
              title="运行环境"
              value={versionInfo.environment}
              prefix={<Tag color={versionInfo.environment === 'production' ? 'gold' : 'cyan'}>{versionInfo.environment}</Tag>}
            />
          </Col>
        </Row>
        <Divider style={{ margin: '16px 0' }} />
        <Descriptions layout="vertical" size="middle">
          <Descriptions.Item label="API Key 状态">
            {versionInfo.apiKeyInlined ? (
              <Badge color="success" text="已内联到前端构建" />
            ) : (
              <Badge color="error" text="运行时从后端获取" />
            )}
          </Descriptions.Item>
          <Descriptions.Item label="完整 Commit">{versionInfo.commit}</Descriptions.Item>
        </Descriptions>
      </Card>
    );
  };

  const renderChanges = () => {
    if (loadingChanges) return <Spin size="large" style={{ display: 'block', margin: '24px auto' }} />;
    if (!recentChanges || recentChanges.length === 0) return <Empty description="暂无变更记录" style={{ padding: 24 }} />;

    return (
      <Card>
        {recentChanges.map((record) => (
          <div key={record.id} style={{ display: 'flex', alignItems: 'flex-start', gap: 12, padding: '12px 0', borderBottom: '1px solid var(--color-border)' }}>
            <div style={{ flexShrink: 0, minWidth: 72 }}>
              <Tag color={record.type === 'feat' ? 'green' : record.type === 'fix' ? 'red' : record.type === 'refactor' ? 'purple' : 'volcano'}>{record.type}</Tag>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 500, marginBottom: 4 }}>{record.message}</div>
              <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>{formatDate(record.date)}</div>
            </div>
          </div>
        ))}
      </Card>
    );
  };

  const renderDeployStatus = () => {
    if (loadingDeploy) return <Spin size="large" style={{ display: 'block', margin: '24px auto' }} />;
    if (!deployStatus) return <Empty description="获取部署状态失败" style={{ padding: 24 }} />;

    const statusItems = [
      { label: 'App 容器', healthy: deployStatus.appHealthy },
      { label: 'Redis 容器', healthy: deployStatus.redisHealthy },
      { label: 'Frontend 容器', healthy: deployStatus.frontendHealthy },
    ];

    return (
      <Card>
        <Row gutter={16}>
          {statusItems.map((item) => (
            <Col key={item.label} xs={24} sm={12} md={8}>
              <Statistic
                title={item.label}
                value={item.healthy ? '正常' : '异常'}
                valueStyle={{
                  color: item.healthy ? 'var(--color-success)' : 'var(--color-error)',
                  fontWeight: 600,
                  fontSize: 16,
                }}
                prefix={<Tag color={item.healthy ? 'success' : 'error'}>{item.healthy ? '●' : '○'}</Tag>}
              />
            </Col>
          ))}
        </Row>
        <Divider style={{ margin: '16px 0' }} />
        <Descriptions layout="vertical" size="middle">
          <Descriptions.Item label="最后部署时间">
            {deployStatus.lastDeploy ? formatDateTime(deployStatus.lastDeploy) : '从未部署'}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    );
  };

  const renderEnvConfig = () => {
    if (loadingEnv) return <Spin size="large" style={{ display: 'block', margin: '24px auto' }} />;
    if (!envConfig) return <Empty description="获取环境配置失败" style={{ padding: 24 }} />;

    const envItems = [
      { key: 'VITE_API_KEY', label: 'VITE_API_KEY', value: envConfig.VITE_API_KEY || '未设置', sensitive: true },
      { key: 'VITE_DEV_MODE', label: 'VITE_DEV_MODE', value: String(envConfig.VITE_DEV_MODE || 'false'), sensitive: false },
      { key: 'VITE_ENABLE_MOCK_FALLBACK', label: 'VITE_ENABLE_MOCK_FALLBACK', value: String(envConfig.VITE_ENABLE_MOCK_FALLBACK || 'false'), sensitive: false },
    ];

    return (
      <Card>
        <Descriptions layout="vertical" size="middle">
          {envItems.map((item) => (
            <Descriptions.Item key={item.key} label={item.label}>
              <Tooltip title={item.sensitive ? '点击复制完整值' : ''}>
                <Tag color={item.sensitive ? 'blue' : 'default'} style={{ cursor: item.sensitive ? 'pointer' : 'default' }}>
                  {item.sensitive && item.value !== '未设置' ? `${item.value.substring(0, 8)}...` : item.value}
                </Tag>
              </Tooltip>
            </Descriptions.Item>
          ))}
        </Descriptions>
      </Card>
    );
  };

  const handleTabChange = (key: string) => {
    setActiveTab(key as VersionControlTab);
  };

  const getTabContent = () => {
    switch (activeTab) {
      case 'current':
        return renderVersionInfo();
      case 'changes':
        return renderChanges();
      case 'deploy':
        return renderDeployStatus();
      case 'env':
        return renderEnvConfig();
      default:
        return null;
    }
  };

  // 计算整体健康度
  const isOverallHealthy = deployStatus?.appHealthy && deployStatus?.redisHealthy && deployStatus?.frontendHealthy;
  const apiStatus = versionInfo ? (versionInfo.apiKeyInlined ? '正常' : '需后端验证') : '未知';

  return (
    <PageContainer>
      <PageHeader title="版本控制" subtitle="系统版本、变更记录与部署状态查看" />

      {/* 顶部关键指标行 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="整体健康度"
              value={isOverallHealthy ? '健康' : '异常'}
              valueStyle={{
                color: isOverallHealthy ? 'var(--color-success)' : 'var(--color-error)',
                fontSize: 20,
                fontWeight: 600,
              }}
              prefix={<Tag color={isOverallHealthy ? 'success' : 'error'}>{isOverallHealthy ? '✓' : '✗'}</Tag>}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="API 认证状态"
              value={apiStatus}
              valueStyle={{ fontSize: 16, fontWeight: 500 }}
              prefix={<Tag color={versionInfo?.apiKeyInlined ? 'success' : 'warning'}>AUTH</Tag>}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="当前版本"
              value={versionInfo?.version || '加载中...'}
              valueStyle={{ fontSize: 16, fontWeight: 500, fontFamily: 'monospace' }}
              prefix={<Tag color="info">VER</Tag>}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="服务器时间 (CST)"
              value={serverTime}
              valueStyle={{ fontSize: 14, fontFamily: 'monospace' }}
              prefix={<Tag color="purple">CST</Tag>}
            />
          </Card>
        </Col>
      </Row>

      {/* 主内容区：Tabs + 右侧快照 */}
      <Row gutter={16}>
        <Col xs={24} lg={16} xxl={18}>
          <Card>
            <Tabs
              defaultActiveKey="current"
              activeKey={activeTab}
              onChange={handleTabChange}
              items={VERSION_CONTROL_TABS}
              type="card"
            >
              {getTabContent()}
            </Tabs>
          </Card>
        </Col>

        <Col xs={24} lg={8} xxl={6}>
          <Card title="系统快照" extra={<Tag color={isOverallHealthy ? 'success' : 'error'}>{isOverallHealthy ? '全部正常' : '存在异常'}</Tag>}>
            <Descriptions layout="vertical" size="small">
              <Descriptions.Item label="App 容器">
                <Badge status={deployStatus?.appHealthy ? 'success' : 'error'} text={deployStatus?.appHealthy ? '正常' : '异常'} />
              </Descriptions.Item>
              <Descriptions.Item label="Redis 容器">
                <Badge status={deployStatus?.redisHealthy ? 'success' : 'error'} text={deployStatus?.redisHealthy ? '正常' : '异常'} />
              </Descriptions.Item>
              <Descriptions.Item label="Frontend 容器">
                <Badge status={deployStatus?.frontendHealthy ? 'success' : 'error'} text={deployStatus?.frontendHealthy ? '正常' : '异常'} />
              </Descriptions.Item>
              <Descriptions.Item label="最后部署">
                {deployStatus?.lastDeploy ? formatDateTime(deployStatus.lastDeploy) : '从未部署'}
              </Descriptions.Item>
              <Descriptions.Item label="环境">{versionInfo?.environment || '未知'}</Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>
    </PageContainer>
  );
};

export default VersionControl;
