import React, { useState, useMemo, useCallback, useEffect } from 'react';
import dayjs from 'dayjs';
import {
  Card,
  Table,
  Input,
  Button,
  Select,
  Space,
  Spin,
  DatePicker,
  message,
  Badge,
  Tag,
  Row,
  Col,
  Statistic,
  Drawer,
  Descriptions,
  Modal,
  Tabs,
  Progress,
  Tooltip,
  Divider,
  Form,
  Switch,
  Alert,
  Empty,
  Dropdown,
  Menu,
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  SettingOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  FileTextOutlined,
  PlayCircleOutlined,
  PieChartOutlined,
  BarChartOutlined,
  LineChartOutlined,
  HistoryOutlined,
  MoreOutlined,
  ShoppingCartOutlined,
} from '@ant-design/icons';
import {
  complianceApi,
  type ComplianceItem,
  type ComplianceViolation,
  type PaginatedResponse,
  type ComplianceStats,
  type ComplianceCheckResult,
  type ComplianceRule,
} from '@/api/index';
import { useApi } from '@/hooks/useApi';
import { formatNumber, formatDateTime } from '@/utils/formatters';
import { PageContainer, PageHeader, TableCard, StatCard } from '@/components/layout';
import styles from './Compliance.module.css';

const { RangePicker } = DatePicker;
type DateRangeValue = [dayjs.Dayjs, dayjs.Dayjs] | null;

const riskLevelColors = {
  high: 'red',
  medium: 'orange',
  low: 'green',
} as const;

const riskLevelLabels = {
  high: '高风险',
  medium: '中风险',
  low: '低风险',
} as const;

const statusColors = {
  pending: 'orange',
  ignored: 'blue',
  resolved: 'green',
} as const;

const statusLabels = {
  pending: '待处理',
  ignored: '已忽略',
  resolved: '已解决',
} as const;

const severityColors = {
  CRITICAL: 'volcano',
  HIGH: 'red',
  MEDIUM: 'orange',
  LOW: 'green',
} as const;

const Compliance = () => {
  const [searchText, setSearchText] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [dateRange, setDateRange] = useState<DateRangeValue>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [activeTab, setActiveTab] = useState<'list' | 'rules'>('list');
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false);
  const [selectedItem, setSelectedItem] = useState<ComplianceItem | null>(null);
  const [checkLoading, setCheckLoading] = useState(false);
  const [ruleDrawerVisible, setRuleDrawerVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<ComplianceRule | null>(null);
  const [rulesLoading, setRulesLoading] = useState(false);

  // Stats API
  const { data: statsData, refetch: refetchStats } = useApi<{ data: ComplianceStats }>(
    complianceApi.getStats,
    [],
    { retryOnError: true }
  );

  // List API
  const { data, status, error, refetch } = useApi<PaginatedResponse<ComplianceItem>>(
    () => complianceApi.getList({
      page,
      size: pageSize,
      keyword: searchText,
      risk_level: riskFilter,
      status: statusFilter,
      start_date: dateRange?.[0]?.format('YYYY-MM-DD'),
      end_date: dateRange?.[1]?.format('YYYY-MM-DD'),
    }),
    [page, pageSize, searchText, riskFilter, statusFilter, dateRange],
    { retryOnError: true }
  );

  // Rules API
  const { data: rulesData, refetch: refetchRules } = useApi<{ data: ComplianceRule[] }>(
    complianceApi.getRules,
    [],
    { retryOnError: true }
  );

  const loading = status === 'loading';
  const stats = statsData?.data;
  const compliance = data?.data || [];
  const total = data?.total || 0;
  const rules = rulesData?.data || [];

  // Refetch stats when list data changes
  useEffect(() => {
    refetchStats();
  }, [refetchStats, data]);

  const handleSearch = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value);
    setPage(1);
  }, []);

  const handleDateChange = useCallback((dates: DateRangeValue) => {
    setDateRange(dates);
    setPage(1);
  }, []);

  const handleRiskChange = useCallback((value: string) => {
    setRiskFilter(value);
    setPage(1);
  }, []);

  const handleStatusChange = useCallback((value: string) => {
    setStatusFilter(value);
    setPage(1);
  }, []);

  const handleTableChange = useCallback((pagination: { current: number; pageSize: number }) => {
    if (pagination) {
      setPage(pagination.current);
      setPageSize(pagination.pageSize);
    }
  }, []);

  const handleViewDetail = useCallback((record: ComplianceItem) => {
    setSelectedItem(record);
    setDetailDrawerVisible(true);
  }, []);

  const handleIgnore = useCallback(async (record: ComplianceItem) => {
    try {
      message.loading('处理中...', 0);
      await complianceApi.ignore(record.product_id);
      message.destroy();
      message.success('已忽略');
      refetch();
    } catch (_err) {
      message.destroy();
      message.error('操作失败');
    }
  }, [refetch]);

  const handleTakeDown = useCallback(async (record: ComplianceItem) => {
    try {
      message.loading('下架中...', 0);
      await complianceApi.takeDown(record.product_id);
      message.destroy();
      message.success('已下架');
      refetch();
    } catch (_err) {
      message.destroy();
      message.error('下架失败');
    }
  }, [refetch]);

  const handleRestore = useCallback(async (record: ComplianceItem) => {
    try {
      message.loading('恢复中...', 0);
      await complianceApi.restore(record.product_id);
      message.destroy();
      message.success('已恢复');
      refetch();
    } catch (_err) {
      message.destroy();
      message.error('恢复失败');
    }
  }, [refetch]);

  const handleTriggerCheck = useCallback(async () => {
    setCheckLoading(true);
    try {
      message.loading('合规检测中...', 0);
      const result = await complianceApi.triggerCheck();
      message.destroy();
      message.success(`检测完成: 共 ${result.data.checked} 个商品, 合规 ${result.data.pass}, 预警 ${result.data.warning}, 不合规 ${result.data.fail}`);
      refetch();
      refetchStats();
    } catch (_err) {
      message.destroy();
      message.error('检测失败');
    } finally {
      setCheckLoading(false);
    }
  }, [refetch, refetchStats]);

  const handleExport = useCallback(async () => {
    try {
      message.loading('导出中...', 0);
      const response = await complianceApi.export({
        keyword: searchText,
        risk_level: riskFilter,
        status: statusFilter,
        start_date: dateRange?.[0]?.format('YYYY-MM-DD'),
        end_date: dateRange?.[1]?.format('YYYY-MM-DD'),
      });
      message.destroy();
      
      const blob = new Blob([response as BlobPart], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `compliance_report_${dayjs().format('YYYYMMDD_HHmmss')}.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
      message.success('导出成功');
    } catch (err) {
      message.destroy();
      message.error('导出失败');
    }
  }, [searchText, riskFilter, statusFilter, dateRange]);

  const handleAddRule = useCallback(() => {
    setEditingRule({
      id: '',
      rule_name: '',
      rule_description: '',
      rule_type: 'KEYWORD',
      rule_content: { keywords: [] },
      is_active: true,
      severity: 'MEDIUM',
      category: '',
      created_at: '',
      updated_at: '',
      created_by: '',
    });
    setRuleDrawerVisible(true);
  }, []);

  const handleEditRule = useCallback((rule: ComplianceRule) => {
    setEditingRule({ ...rule });
    setRuleDrawerVisible(true);
  }, []);

  const handleDeleteRule = useCallback(async (ruleId: string) => {
    try {
      await complianceApi.deleteRule(ruleId);
      message.success('规则已删除');
      refetchRules();
    } catch (_err) {
      message.error('删除失败');
    }
  }, [refetchRules]);

  const handleRuleSubmit = useCallback(async (values: Partial<ComplianceRule>) => {
    try {
      setRulesLoading(true);
      const ruleId = editingRule?.id;
      if (ruleId) {
        await complianceApi.updateRule(ruleId, values);
        message.success('规则已更新');
      } else {
        await complianceApi.createRule(values as Partial<ComplianceRule>);
        message.success('规则已创建');
      }
      setRuleDrawerVisible(false);
      setEditingRule(null);
      refetchRules();
    } catch (_err) {
      message.error('保存失败');
    } finally {
      setRulesLoading(false);
    }
  }, [editingRule, refetchRules]);

  const getRiskBadge = (level: string) => (
    <Badge status={(riskLevelColors[level as keyof typeof riskLevelColors] || 'default') as 'error' | 'warning' | 'success' | 'default' | 'processing'} text={riskLevelLabels[level as keyof typeof riskLevelLabels] || level} />
  );

  const getStatusTag = (status: string) => (
    <Tag color={statusColors[status as keyof typeof statusColors] || 'default'}>
      {statusLabels[status as keyof typeof statusLabels] || status}
    </Tag>
  );

  const getSeverityTag = (severity: string) => (
    <Tag color={severityColors[severity as keyof typeof severityColors] || 'default'}>
      {severity}
    </Tag>
  );

  const columns = useMemo(() => [
    {
      title: '商品ID',
      dataIndex: 'product_id',
      key: 'product_id',
      width: 120,
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 220,
      ellipsis: true,
      onCell: (record: ComplianceItem) => ({
        onClick: () => handleViewDetail(record),
        style: { cursor: 'pointer' },
      }),
    },
    {
      title: '风险等级',
      dataIndex: 'risk_level',
      key: 'risk_level',
      width: 100,
      align: 'center' as const,
      render: getRiskBadge,
    },
    {
      title: '合规分数',
      dataIndex: 'compliance_score',
      key: 'compliance_score',
      width: 100,
      align: 'center' as const,
      render: (score: number) => (
        <Progress
          type="circle"
          width={60}
          percent={score}
          strokeColor={score >= 80 ? '#52c41a' : score >= 60 ? '#faad14' : '#ff4d4f'}
          format={() => `${score}`}
        />
      ),
    },
    {
      title: '违规类型',
      dataIndex: 'violation_type',
      key: 'violation_type',
      width: 140,
    },
    {
      title: '违规详情',
      dataIndex: 'violation_detail',
      key: 'violation_detail',
      width: 250,
      ellipsis: true,
    },
    {
      title: '检测时间',
      dataIndex: 'detected_at',
      key: 'detected_at',
      width: 180,
      render: formatDateTime,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      align: 'center' as const,
      render: getStatusTag,
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record: ComplianceItem) => {
        const menuItems = [
          { key: 'detail', label: <span><EyeOutlined /> 查看详情</span>, onClick: () => handleViewDetail(record) },
          { type: 'divider' as const },
          ...(record.status === 'pending' ? [
            { key: 'ignore', label: <span>忽略</span>, onClick: () => handleIgnore(record) },
            { key: 'takeDown', label: <span><CloseCircleOutlined /> 下架商品</span>, onClick: () => handleTakeDown(record), danger: true },
          ] : record.status === 'ignored' ? [
            { key: 'restore', label: <span><CheckCircleOutlined /> 恢复</span>, onClick: () => handleRestore(record) },
          ] : []),
          { type: 'divider' as const },
          { key: 'history', label: <span><HistoryOutlined /> 检测历史</span>, onClick: () => handleViewDetail(record) },
        ];
        return (
          <Dropdown
            menu={{ items: menuItems }}
            trigger={['click']}
            placement="bottomRight"
          >
            <Button type="link" size="small">
              <MoreOutlined /> 操作
            </Button>
          </Dropdown>
        );
      },
    },
  ], [handleViewDetail, handleIgnore, handleTakeDown, handleRestore]);

  const ruleColumns = useMemo(() => [
    {
      title: '规则ID',
      dataIndex: 'id',
      key: 'id',
      width: 150,
    },
    {
      title: '规则名称',
      dataIndex: 'rule_name',
      key: 'rule_name',
      width: 200,
    },
    {
      title: '类型',
      dataIndex: 'rule_type',
      key: 'rule_type',
      width: 100,
      align: 'center' as const,
      render: (type: string) => <Tag>{type}</Tag>,
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      align: 'center' as const,
      render: getSeverityTag,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      align: 'center' as const,
      render: (active: boolean) => (
        <Switch
          checked={active}
          onChange={(checked) => handleRuleSubmit({ ...editingRule, id: editingRule?.id, is_active: checked })}
          loading={rulesLoading}
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: formatDateTime,
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_, record: ComplianceRule) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEditRule(record)}>编辑</Button>
          <Button type="link" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteRule(record.id)}>删除</Button>
        </Space>
      ),
    },
  ], [handleEditRule, handleDeleteRule, handleRuleSubmit, editingRule, rulesLoading]);

  const renderStatCards = () => {
    if (!stats) return null;
    return (
      <Row gutter={[16, 16]} className={styles.statsRow}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            label="总商品数"
            value={stats.total_products}
            prefix={<ShoppingCartOutlined style={{ color: '#1890ff' }} />}
            subValue={`已检测 ${stats.checked_products}`}
            subLabel="检测覆盖"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            label="合规率"
            value={stats.compliance_rate}
            suffix="%"
            prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            subValue={`合格 ${stats.pass_count} / 预警 ${stats.warning_count} / 不合格 ${stats.fail_count}`}
            subLabel="详细分布"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            label="高风险商品"
            value={stats.fail_count}
            prefix={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
            subValue={`中风险 ${stats.warning_count} / 低风险 ${stats.pass_count}`}
            subLabel="风险分布"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            label="待处理数量"
            value={stats.status_distribution?.pending || 0}
            prefix={<WarningOutlined style={{ color: '#faad14' }} />}
            subValue={`已忽略 ${stats.status_distribution?.ignored || 0} / 已解决 ${stats.status_distribution?.resolved || 0}`}
            subLabel="处理状态"
          />
        </Col>
      </Row>
    );
  };

  const renderRiskDistributionChart = () => {
    if (!stats) return null;
    const { high, medium, low } = stats.risk_distribution;
    const total = high + medium + low;
    if (total === 0) return <Empty description="暂无风险分布数据" />;
    return (
      <Card title="风险等级分布" className={styles.chartCard}>
        <div className={styles.chartContainer}>
          <div className={styles.chartLegend}>
            <div className={styles.legendItem}>
              <span className={styles.legendColor} style={{ background: '#ff4d4f' }} />
              <span>高风险 ({high})</span>
            </div>
            <div className={styles.legendItem}>
              <span className={styles.legendColor} style={{ background: '#faad14' }} />
              <span>中风险 ({medium})</span>
            </div>
            <div className={styles.legendItem}>
              <span className={styles.legendColor} style={{ background: '#52c41a' }} />
              <span>低风险 ({low})</span>
            </div>
          </div>
          <div className={styles.chartBars}>
            <div className={styles.barWrapper}>
              <div
                className={styles.bar}
                style={{
                  height: `${total > 0 ? (high / total) * 100 : 0}%`,
                  background: '#ff4d4f',
                }}
              />
              <span className={styles.barLabel}>高风险</span>
            </div>
            <div className={styles.barWrapper}>
              <div
                className={styles.bar}
                style={{
                  height: `${total > 0 ? (medium / total) * 100 : 0}%`,
                  background: '#faad14',
                }}
              />
              <span className={styles.barLabel}>中风险</span>
            </div>
            <div className={styles.barWrapper}>
              <div
                className={styles.bar}
                style={{
                  height: `${total > 0 ? (low / total) * 100 : 0}%`,
                  background: '#52c41a',
                }}
              />
              <span className={styles.barLabel}>低风险</span>
            </div>
          </div>
        </div>
      </Card>
    );
  };

  const renderStatusDistributionChart = () => {
    if (!stats) return null;
    const { pending, ignored, resolved } = stats.status_distribution;
    const total = pending + ignored + resolved;
    if (total === 0) return <Empty description="暂无状态分布数据" />;
    return (
      <Card title="处理状态分布" className={styles.chartCard}>
        <div className={styles.chartContainer}>
          <div className={styles.chartLegend}>
            <div className={styles.legendItem}>
              <span className={styles.legendColor} style={{ background: '#faad14' }} />
              <span>待处理 ({pending})</span>
            </div>
            <div className={styles.legendItem}>
              <span className={styles.legendColor} style={{ background: '#1890ff' }} />
              <span>已忽略 ({ignored})</span>
            </div>
            <div className={styles.legendItem}>
              <span className={styles.legendColor} style={{ background: '#52c41a' }} />
              <span>已解决 ({resolved})</span>
            </div>
          </div>
          <div className={styles.chartBars}>
            <div className={styles.barWrapper}>
              <div
                className={styles.bar}
                style={{
                  height: `${total > 0 ? (pending / total) * 100 : 0}%`,
                  background: '#faad14',
                }}
              />
              <span className={styles.barLabel}>待处理</span>
            </div>
            <div className={styles.barWrapper}>
              <div
                className={styles.bar}
                style={{
                  height: `${total > 0 ? (ignored / total) * 100 : 0}%`,
                  background: '#1890ff',
                }}
              />
              <span className={styles.barLabel}>已忽略</span>
            </div>
            <div className={styles.barWrapper}>
              <div
                className={styles.bar}
                style={{
                  height: `${total > 0 ? (resolved / total) * 100 : 0}%`,
                  background: '#52c41a',
                }}
              />
              <span className={styles.barLabel}>已解决</span>
            </div>
          </div>
        </div>
      </Card>
    );
  };

  const renderDetailDrawer = () => (
    <Drawer
      title="商品合规详情"
      placement="right"
      closable
      onClose={() => setDetailDrawerVisible(false)}
      visible={detailDrawerVisible}
      width={720}
      size="large"
    >
      {selectedItem && (
        <Descriptions column={2} title="基本信息" bordered>
          <Descriptions.Item label="商品ID">{selectedItem.product_id}</Descriptions.Item>
          <Descriptions.Item label="商品名称">{selectedItem.product_name}</Descriptions.Item>
          <Descriptions.Item label="风险等级">{getRiskBadge(selectedItem.risk_level)}</Descriptions.Item>
          <Descriptions.Item label="合规分数">
            <Progress
              type="circle"
              width={60}
              percent={Number(selectedItem.compliance_score) || 0}
              strokeColor={
                (Number(selectedItem.compliance_score) || 0) >= 80
                  ? '#52c41a'
                  : (Number(selectedItem.compliance_score) || 0) >= 60
                  ? '#faad14'
                  : '#ff4d4f'
              }
              format={() => `${Number(selectedItem.compliance_score) || 0}`}
            />
          </Descriptions.Item>
          <Descriptions.Item label="违规类型">{selectedItem.violation_type}</Descriptions.Item>
          <Descriptions.Item label="检测时间">{formatDateTime(selectedItem.detected_at)}</Descriptions.Item>
          <Descriptions.Item label="处理状态">{getStatusTag(selectedItem.status)}</Descriptions.Item>
          <Descriptions.Item label="违规详情" span={2}>{selectedItem.violation_detail}</Descriptions.Item>
          {(selectedItem.violations && Array.isArray(selectedItem.violations) && selectedItem.violations.length > 0) && (
            <Descriptions.Item label="违规明细" span={2}>
              <div className={styles.violationsList}>
                {selectedItem.violations.map((v, idx) => (
                  <div key={idx} className={styles.violationItem}>
                    <div className={styles.violationHeader}>
                      <span className={styles.violationRule}>{v.rule_name}</span>
                      {getSeverityTag(v.severity)}
                    </div>
                    <div className={styles.violationDetail}>{v.violation_detail}</div>
                    <div className={styles.violationMeta}>
                      <span>类别: {v.category}</span>
                      <span>匹配词: {v.matched_keywords && Array.isArray(v.matched_keywords) ? v.matched_keywords.join(', ') : '无'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Descriptions.Item>
          )}
          <Descriptions.Item label="检测批次" span={2}>{selectedItem.check_batch_id}</Descriptions.Item>
        </Descriptions>
      )}
    </Drawer>
  );

  const renderRuleDrawer = () => (
    <Drawer
      title={editingRule?.id ? '编辑合规规则' : '新建合规规则'}
      placement="right"
      closable
      onClose={() => { setRuleDrawerVisible(false); setEditingRule(null); }}
      visible={ruleDrawerVisible}
      width={680}
      size="large"
    >
      <Form
        layout="vertical"
        onFinish={handleRuleSubmit}
        initialValues={{
          rule_type: 'KEYWORD',
          is_active: true,
          severity: 'MEDIUM',
          rule_content: { keywords: [] },
        }}
      >
        <Form.Item name="rule_name" label="规则名称" rules={[{ required: true, message: '请输入规则名称' }]}>
          <Input placeholder="请输入规则名称" />
        </Form.Item>
        <Form.Item name="rule_description" label="规则描述">
          <Input.TextArea placeholder="请输入规则描述" rows={2} />
        </Form.Item>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="rule_type" label="规则类型" rules={[{ required: true }]}>
              <Select>
                <Select.Option value="KEYWORD">关键词匹配</Select.Option>
                <Select.Option value="REGEX">正则表达式</Select.Option>
                <Select.Option value="ML_MODEL">机器学习模型</Select.Option>
                <Select.Option value="CUSTOM_SCRIPT">自定义脚本</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="severity" label="严重程度" rules={[{ required: true }]}>
              <Select>
                <Select.Option value="LOW">低</Select.Option>
                <Select.Option value="MEDIUM">中</Select.Option>
                <Select.Option value="HIGH">高</Select.Option>
                <Select.Option value="CRITICAL">严重</Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>
        <Col span={12}>
          <Form.Item name="category" label="规则分类" rules={[{ required: true, message: '请输入规则分类' }]}>
            <Input placeholder="如: 广告法、医疗广告、知识产权、食品安全、价格宣传" />
          </Form.Item>
        </Col>
        <Form.Item
          name={['rule_content', 'keywords']}
          label="规则内容"
          rules={[{ required: true, message: '请输入规则内容' }]}
        >
          <Input.TextArea
            placeholder="关键词匹配模式: 每行一个关键词&#10;正则表达式模式: 每行一个正则表达式"
            rows={6}
          />
        </Form.Item>
        <Form.Item name="is_active" valuePropName="checked" label="启用规则">
          <Switch />
        </Form.Item>
        <Divider />
        <Space>
          <Button htmlType="submit" type="primary" loading={rulesLoading} icon={<CheckCircleOutlined />}>
            {editingRule?.id ? '保存' : '创建'}
          </Button>
          <Button onClick={() => { setRuleDrawerVisible(false); setEditingRule(null); }}>取消</Button>
        </Space>
      </Form>
    </Drawer>
  );

  return (
    <PageContainer>
      <PageHeader
        title="商品合规管理"
        subtitle="监控商品合规状态，自动检测违规内容，管理合规规则"
        filters={
          <Space wrap className={styles.filters}>
            <Input
              placeholder="搜索商品名称/ID..."
              value={searchText}
              onChange={handleSearch}
              prefix={<SearchOutlined />}
              style={{ width: 250 }}
              allowClear
            />
            <RangePicker
              value={dateRange}
              onChange={handleDateChange}
              placeholder={['开始日期', '结束日期']}
              style={{ width: 300 }}
              allowClear
            />
            <Select
              placeholder="风险等级"
              value={riskFilter}
              onChange={handleRiskChange}
              allowClear
              style={{ width: 140 }}
              options={[
                { value: 'high', label: '高风险' },
                { value: 'medium', label: '中风险' },
                { value: 'low', label: '低风险' },
              ]}
            />
            <Select
              placeholder="处理状态"
              value={statusFilter}
              onChange={handleStatusChange}
              allowClear
              style={{ width: 140 }}
              options={[
                { value: 'pending', label: '待处理' },
                { value: 'ignored', label: '已忽略' },
                { value: 'resolved', label: '已解决' },
              ]}
            />
          </Space>
        }
        actions={
          <Space>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>导出 CSV</Button>
            <Button icon={<SettingOutlined />} onClick={handleAddRule}>规则管理</Button>
            <Button
              icon={<PlayCircleOutlined />}
              type="primary"
              onClick={handleTriggerCheck}
              loading={checkLoading}
            >
              一键检测
            </Button>
            <Button icon={<ReloadOutlined />} onClick={refetch} loading={loading}>刷新</Button>
          </Space>
        }
      />

      {renderStatCards()}

      <Row gutter={[16, 16]} className={styles.chartsRow}>
        <Col xs={24} lg={12}>
          {renderRiskDistributionChart()}
        </Col>
        <Col xs={24} lg={12}>
          {renderStatusDistributionChart()}
        </Col>
      </Row>

      <Tabs activeKey={activeTab} onChange={(key) => { setActiveTab(key as 'list' | 'rules'); if (key === 'rules') refetchRules(); }} className={styles.tabs}>
        <Tabs.TabPane tab={<span><FileTextOutlined /> 合规列表</span>} key="list" />
        <Tabs.TabPane tab={<span><SettingOutlined /> 规则管理</span>} key="rules" />
      </Tabs>

      {activeTab === 'list' && (
        <TableCard<ComplianceItem>
          dataSource={compliance}
          columns={columns}
          rowKey="product_id"
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total: number) => `共 ${total} 条`,
          }}
          onTableChange={handleTableChange}
          loading={loading}
          error={error}
          scroll={{ x: 1400 }}
          size="middle"
        />
      )}

      {activeTab === 'rules' && (
        <Card title="合规规则配置" className={styles.rulesCard}>
          <Alert
            message="合规检测引擎基于关键词匹配和正则表达式，支持多种规则类型。新增/编辑规则后会在下次检测时生效。"
            type="info"
            showIcon
            className={styles.rulesAlert}
          />
          <TableCard<ComplianceRule>
            dataSource={rules}
            columns={ruleColumns}
            rowKey="id"
            pagination={false}
            loading={rulesLoading}
            size="middle"
          />
        </Card>
      )}

      {renderDetailDrawer()}
      {renderRuleDrawer()}
    </PageContainer>
  );
};

export default Compliance;