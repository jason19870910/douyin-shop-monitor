import { useMemo, useState } from 'react';
import {
  Row, Col, Card, Tabs, Tag, Drawer, Descriptions, Button, Space, Empty,
  Table, Switch, Modal, Form, Input, Select, Popconfirm, message, Skeleton, Tooltip,
  Dropdown, Checkbox,
} from 'antd';
import { PlusOutlined, SafetyCertificateOutlined, RestOutlined } from '@ant-design/icons';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip as ChartTooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import type { ColumnsType } from 'antd/es/table';
import { formatNumber, formatDate } from '@/utils/formatters';
import { complianceApi, type ComplianceItem, type ComplianceRule, type ComplianceCheckResult } from '@/api/index';
import { colors } from '@/theme/tokens';
import {
  queryKeys, useComplianceStats, useComplianceRules, useComplianceRuleHistory, useComplianceList,
  useIgnoreCompliance, useTakeDownCompliance, useRestoreCompliance,
  useCheckProductsCompliance, useCheckWorksCompliance, useCreateComplianceRule, useUpdateComplianceRule, useDeleteComplianceRule,
} from '@/hooks/useQueries';
import { DataTable, type DataTableColumn } from '@/components/common';
import { PageContainer, PageHeader } from '@/components/layout';

const STATUS_META: Record<string, { color: string; label: string }> = {
  pass: { color: 'green', label: '通过' },
  fail: { color: 'red', label: '失败' },
  warning: { color: 'orange', label: '告警' },
  ignored: { color: 'default', label: '已忽略' },
  taken_down: { color: 'purple', label: '已下架' },
  restored: { color: 'blue', label: '已恢复' },
};

const SEVERITY_META: Record<string, { color: string; label: string }> = {
  LOW: { color: 'green', label: '低' },
  MEDIUM: { color: 'orange', label: '中' },
  HIGH: { color: 'red', label: '高' },
  CRITICAL: { color: 'magenta', label: '严重' },
};

const RULE_TYPE_OPTIONS = [
  'KEYWORD', 'REGEX', 'PRICE', 'LICENSE', 'ML_MODEL', 'CUSTOM_SCRIPT',
  'HAOHUO_IMAGE', 'HAOHUO_SPEC', 'HAOHUO_PRICE', 'HAOHUO_FATAL'
];
const SEVERITY_OPTIONS = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
const APPLICABLE_TO_OPTIONS = [
  { label: '商品', value: 'product' },
  { label: '作品', value: 'work' },
];
const PIE_COLORS = [
  colors.success[500],      // #52c41a - 通过
  colors.error[500],        // #ff4d4f - 失败
  colors.warning[500],      // #faad14 - 告警
  colors.neutral[500],      // #8c8c8c - 已忽略
  '#722ed1',                // Purple - 已下架 (not in tokens)
  colors.primary[500],      // #66A3FF - 已恢复 (replaces #1677ff)
];

const latestTime = (item: ComplianceItem): string | undefined =>
  item.taken_down_at || item.restored_at || item.ignored_at || item.created_at || item.updated_at;

interface RuleFormValues {
  rule_name: string;
  rule_type: ComplianceRule['rule_type'];
  severity: ComplianceRule['severity'];
  category: string;
  enabled: boolean;
  applicable_to: ('product' | 'work')[];
  content: string;
}

const parseRuleContent = (values: RuleFormValues): Record<string, unknown> => {
  const text = values.content.trim();
  if (!text) return {};
  if (values.rule_type === 'KEYWORD') {
    return { keywords: text.split(/[,，\s]+/).filter(Boolean) };
  }
  if (values.rule_type === 'REGEX') {
    return { pattern: text };
  }
  // ⭐ 新增：product 规则可使用 JSON 内容，包含 category 字段
  try {
    const parsed = JSON.parse(text);
    // 确保有 category 字段（用于筛选/分类）
    if (parsed.category) return parsed;
    // 如果是 product 类型的规则，默认赋予 '内容合规' 分类
    return { ...parsed, category: parsed.category || '内容合规' };
  } catch {
    return { value: text, category: '内容合规' };
  }
};

const stringifyRuleContent = (rule: ComplianceRule): string => {
  const content = rule.rule_content || {};
  if (Array.isArray(content.keywords)) return (content.keywords as unknown[]).map(String).join(', ');
  if (typeof content.pattern === 'string') return content.pattern;
  const keys = Object.keys(content);
  if (keys.length === 0) return '';
  try {
    return JSON.stringify(content, null, 2);
  } catch {
    return '';
  }
};

const Compliance = () => {
  const [activeTab, setActiveTab] = useState('violations');
  const [detailItem, setDetailItem] = useState<ComplianceItem | null>(null);
  const [ruleModalOpen, setRuleModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<ComplianceRule | null>(null);
  const [historyRuleId, setHistoryRuleId] = useState('');
  const [form] = Form.useForm<RuleFormValues>();

  const { data: stats, isLoading: statsLoading } = useComplianceStats();
  const { data: rulesData, isLoading: rulesLoading } = useComplianceRules();
  const { data: historyData, isLoading: historyLoading } = useComplianceRuleHistory(historyRuleId);
  const { data: complianceItemsData } = useComplianceList({});

  const ignoreMutation = useIgnoreCompliance();
  const takeDownMutation = useTakeDownCompliance();
  const restoreMutation = useRestoreCompliance();
  const checkProducts = useCheckProductsCompliance();
  const checkWorks = useCheckWorksCompliance();
  const createRule = useCreateComplianceRule();
  const updateRule = useUpdateComplianceRule();
  const deleteRule = useDeleteComplianceRule();

  const rules = rulesData?.items || [];
  const complianceItems = complianceItemsData?.items || [];
  const productComplianceItems = complianceItems.filter(item => item.target_type === 'product');

  const statusPieData = useMemo(() => {
    if (!stats) return [];
    return (['passed', 'failed', 'warning', 'ignored', 'taken_down'] as const)
      .map((key) => ({ name: STATUS_META[key === 'passed' ? 'pass' : key === 'failed' ? 'fail' : key]?.label || key, value: Number(stats[key]) || 0, key }))
      .filter((d) => d.value > 0);
  }, [stats]);

  const categoryBarData = useMemo(() => {
    if (!stats?.by_category) return [];
    return Object.entries(stats.by_category).map(([name, count]) => ({ name, count: Number(count) || 0 }));
  }, [stats]);

  const handleAction = (
    mutation: { mutateAsync: (id: string) => Promise<unknown>; isPending?: boolean },
    id: string,
    successText: string,
  ) => {
    mutation.mutateAsync(id).then(
      () => message.success(successText),
      (err: unknown) => message.error(err instanceof Error ? err.message : '操作失败'),
    );
  };

  const refreshCache = async () => {
    message.info('正在刷新合规缓存...');
    const result = await complianceApi.refresh();
    if (result?.refreshed) {
      message.success('合规缓存刷新成功');
      // 刷新页面以显示最新数据
      setTimeout(() => window.location.reload(), 1500);
    } else {
      message.error('刷新失败');
    }
  };

  const handleCheckProducts = () => {
    checkProducts.mutateAsync().then(
      (result: ComplianceCheckResult) => message.success(result.message ?? '商品合规检测已完成'),
      (err: unknown) => message.error(err instanceof Error ? err.message : '检测失败'),
    );
  };

  const handleCheckWorks = () => {
    checkWorks.mutateAsync().then(
      (result: ComplianceCheckResult) => message.success(result.message ?? '作品合规检测已完成'),
      (err: unknown) => message.error(err instanceof Error ? err.message : '检测失败'),
    );
  };

  const openCreateRule = () => {
    setEditingRule(null);
    form.resetFields();
    form.setFieldsValue({
      rule_type: 'KEYWORD',
      severity: 'MEDIUM',
      category: '通用',
      enabled: true,
      applicable_to: ['product'],
      content: '',
    });
    setRuleModalOpen(true);
  };

  const openEditRule = (rule: ComplianceRule) => {
    setEditingRule(rule);
    form.setFieldsValue({
      rule_name: rule.rule_name,
      rule_type: rule.rule_type,
      severity: rule.severity,
      category: rule.category,
      enabled: rule.enabled,
      applicable_to: rule.applicable_to || ['product'],
      content: stringifyRuleContent(rule),
    });
    setRuleModalOpen(true);
  };

  const handleRuleSubmit = () => {
    form.validateFields().then((values) => {
      const payload = {
        rule_name: values.rule_name,
        rule_type: values.rule_type,
        severity: values.severity,
        category: values.category,
        enabled: values.enabled,
        applicable_to: values.applicable_to,
        rule_content: parseRuleContent(values),
      };
      const action = editingRule
        ? updateRule.mutateAsync({ id: editingRule.id, rule: payload })
        : createRule.mutateAsync(payload);
      action.then(
        () => {
          message.success(editingRule ? '规则已更新' : '规则已创建');
          setRuleModalOpen(false);
        },
        (err: unknown) => message.error(err instanceof Error ? err.message : '保存失败'),
      );
    });
  };

  const violationColumns = useMemo<DataTableColumn<ComplianceItem>[]>(() => [
    { title: '记录ID', dataIndex: 'id', key: 'id', width: 150, ellipsis: true },
    {
      title: '目标类型', dataIndex: 'target_type', key: 'target_type', width: 110,
      render: (v: unknown) => (v ? <Tag>{String(v)}</Tag> : '-'),
    },
    {
      title: '关联规则', dataIndex: 'rule_id', key: 'rule_id', width: 130, ellipsis: true,
      render: (v: unknown) => (v ? String(v) : '-'),
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 100, align: 'center',
      render: (v: unknown) => {
        const status = String(v || '');
        const meta = STATUS_META[status];
        return meta ? <Tag color={meta.color}>{meta.label}</Tag> : <Tag>{status || '-'}</Tag>;
      },
    },
    {
      title: '处理时间', dataIndex: 'taken_down_at', key: 'handled_at', width: 170,
      render: (_: unknown, record: ComplianceItem) => {
        const time = latestTime(record);
        return time ? formatDate(time) : '-';
      },
    },
    {
      title: '操作', dataIndex: 'id', key: 'actions', width: 210,
      render: (_: unknown, record: ComplianceItem) => (
        <Space size={4}>
          <Button type="link" size="small" onClick={() => setDetailItem(record)}>详情</Button>
          {record.status !== 'ignored' && (
            <Button type="link" size="small" onClick={() => handleAction(ignoreMutation, record.id, '已忽略')}>忽略</Button>
          )}
          {record.status !== 'taken_down' && (
            <Button type="link" size="small" danger onClick={() => handleAction(takeDownMutation, record.id, '已下架')}>下架</Button>
          )}
          {record.status === 'taken_down' && (
            <Button type="link" size="small" onClick={() => handleAction(restoreMutation, record.id, '已恢复')}>恢复</Button>
          )}
        </Space>
      ),
    },
  ], [ignoreMutation, takeDownMutation, restoreMutation]);

  const ruleTableColumns = useMemo<ColumnsType<ComplianceRule>>(() => [
    { title: '规则名称', dataIndex: 'rule_name', key: 'rule_name', width: 200, ellipsis: true },
    {
      title: '类型', dataIndex: 'rule_type', key: 'rule_type', width: 110,
      render: (v: unknown) => <Tag color="blue">{String(v)}</Tag>,
    },
    {
      title: '严重程度', dataIndex: 'severity', key: 'severity', width: 100, align: 'center',
      render: (v: unknown) => {
        const meta = SEVERITY_META[String(v)];
        return meta ? <Tag color={meta.color}>{meta.label}</Tag> : <Tag>{String(v)}</Tag>;
      },
    },
    { title: '分类', dataIndex: 'category', key: 'category', width: 110 },
    {
      title: '适用对象', dataIndex: 'applicable_to', key: 'applicable_to', width: 140,
      render: (v: unknown) => {
        const list = Array.isArray(v) ? (v as string[]) : [];
        if (list.length === 0) return <Tag>未设置</Tag>;
        return <Space size={4}>{list.map((item) => <Tag key={item} color={item === 'product' ? 'green' : 'orange'}>{item === 'product' ? '商品' : '作品'}</Tag>)}</Space>;
      },
    },
    {
      title: '规则内容', dataIndex: 'rule_content', key: 'rule_content', width: 200, ellipsis: true,
      render: (_: unknown, record: ComplianceRule) => {
        const text = stringifyRuleContent(record);
        return text ? <Tooltip title={text}><span>{text}</span></Tooltip> : '-';
      },
    },
    {
      title: '启用', dataIndex: 'enabled', key: 'enabled', width: 80, align: 'center',
      render: (v: unknown, record: ComplianceRule) => (
        <Switch
          checked={!!v}
          onChange={(checked: boolean) => updateRule.mutate({ id: record.id, rule: { enabled: checked } })}
        />
      ),
    },
    {
      title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', width: 170,
      render: (v: unknown) => (v ? formatDate(String(v)) : '-'),
    },
    {
      title: '操作', key: 'actions', width: 150,
      render: (_: unknown, record: ComplianceRule) => (
        <Space size={4}>
          <Button type="link" size="small" onClick={() => openEditRule(record)}>编辑</Button>
          <Button type="link" size="small" onClick={() => setHistoryRuleId(record.id)}>历史</Button>
          <Popconfirm title="确定删除该规则？" onConfirm={() => deleteRule.mutate(record.id)}>
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ], [updateRule, deleteRule]);

  const statCards = useMemo(() => {
    if (!stats) return [];
    return [
      { label: '总检查数', value: stats.total_checks, color: colors.primary[500] },
      { label: '通过', value: stats.passed, color: colors.success[500] },
      { label: '失败', value: stats.failed, color: colors.error[500] },
      { label: '告警', value: stats.warning, color: colors.warning[500] },
    ];
  }, [stats]);

  return (
    <PageContainer>
      <PageHeader
        title="合规管理"
        subtitle="商品合规检查、违规处理与规则管理"
        actions={
          <Space>
            <Button
              type="text"
              icon={<RestOutlined />}
              onClick={refreshCache}
              disabled={checkProducts.isPending || checkWorks.isPending}
            >
              刷新缓存
            </Button>
            <Button icon={<PlusOutlined />} onClick={openCreateRule}>新建规则</Button>
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'product',
                    label: '检测商品',
                    icon: <SafetyCertificateOutlined />,
                    onClick: handleCheckProducts,
                    disabled: checkProducts.isPending,
                  },
                  {
                    key: 'work',
                    label: '检测作品',
                    icon: <SafetyCertificateOutlined />,
                    onClick: handleCheckWorks,
                    disabled: checkWorks.isPending,
                  },
                  {
                    key: 'all',
                    label: '全部检测',
                    icon: <SafetyCertificateOutlined />,
                    onClick: () => {
                      handleCheckProducts();
                      handleCheckWorks();
                    },
                    disabled: checkProducts.isPending || checkWorks.isPending,
                  },
                ],
              }}
              placement="bottomRight"
            >
              <Button
                type="primary"
                icon={<SafetyCertificateOutlined />}
                loading={checkProducts.isPending || checkWorks.isPending}
              >
                一键合规检测
              </Button>
            </Dropdown>
          </Space>
        }
      />

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {statCards.map((card) => (
          <Col key={card.label} xs={12} sm={12} lg={6}>
            <Card size="small">
              {statsLoading ? (
                <Skeleton paragraph={{ rows: 1 }} />
              ) : (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--color-text-secondary)' }}>{card.label}</span>
                  <span style={{ fontSize: 24, fontWeight: 600, color: card.color }}>{formatNumber(card.value)}</span>
                </div>
              )}
            </Card>
          </Col>
        ))}
        <Col xs={24} lg={12}>
          <Card title="状态分布" size="small">
            {statsLoading ? (
              <Skeleton paragraph={{ rows: 4 }} />
            ) : statusPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={statusPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={75} label>
                    {statusPieData.map((entry, index) => (
                      <Cell key={entry.key} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <ChartTooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="暂无检查数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="分类分布" size="small">
            {statsLoading ? (
              <Skeleton paragraph={{ rows: 4 }} />
            ) : categoryBarData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={categoryBarData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis allowDecimals={false} />
                  <ChartTooltip />
                  <Bar dataKey="count" fill={colors.primary[500]} name="检查数" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="暂无分类数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Col>
      </Row>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'violations',
            label: '违规列表',
            children: (
              <DataTable<ComplianceItem>
                title="合规检查记录"
                queryKey={queryKeys.compliance.list({})}
                queryFn={(params) => complianceApi.getList(params) as Promise<{ items: ComplianceItem[]; total: number }>}
                columns={violationColumns}
                rowKey="id"
                search={{ placeholder: '搜索记录/规则...' }}
                defaultPageSize={20}
                exportConfig={{
                  filenamePrefix: 'compliance',
                  columns: [
                    { key: 'id', label: '记录ID' },
                    { key: 'target_type', label: '目标类型' },
                    { key: 'rule_id', label: '关联规则' },
                    { key: 'status', label: '状态' },
                    { key: 'productId', label: '产品ID' },
                    { key: 'product_title', label: '产品标题' },
                    { key: 'created_at', label: '创建时间' },
                    { key: 'taken_down_at', label: '下架时间' },
                    { key: 'restored_at', label: '恢复时间' },
                  ],
                }}
              />
            ),
          },
          {
            key: 'product',
            label: `商品合规 (${productComplianceItems.length})`,
            children: (
              <Card size="small">
                <Table<ComplianceItem>
                  dataSource={productComplianceItems}
                  columns={[
                    { title: '记录ID', dataIndex: 'id', key: 'id', ellipsis: true },
                    {
                      title: '目标类型', dataIndex: 'target_type', key: 'target_type', width: 110,
                      render: (v: unknown) => (v ? <Tag>{String(v)}</Tag> : '-'),
                    },
                    {
                      title: '产品ID', dataIndex: 'productId', key: 'productId', width: 150,
                      render: (v: unknown) => (v ? <Tag>{String(v)}</Tag> : '-'),
                    },
                    {
                      title: '产品标题', dataIndex: 'product_title', key: 'product_title', width: 200,
                      render: (v: unknown) => (v ? <Tooltip title={String(v)}><span>{String(v)}</span></Tooltip> : '-'),
                    },
                    {
                      title: '状态', dataIndex: 'status', key: 'status', width: 100, align: 'center',
                      render: (v: unknown) => {
                        const status = String(v || '');
                        const meta = STATUS_META[status];
                        return meta ? <Tag color={meta.color}>{meta.label}</Tag> : <Tag>{status || '-'}</Tag>;
                      },
                    },
                    {
                      title: '关联规则', dataIndex: 'rule_id', key: 'rule_id', width: 130, ellipsis: true,
                      render: (v: unknown) => (v ? String(v) : '-'),
                    },
                    {
                      title: '风险等级', dataIndex: 'risk_level', key: 'risk_level', width: 100, align: 'center',
                      render: (v: unknown) => {
                        const meta = SEVERITY_META[String(v)];
                        return meta ? <Tag color={meta.color}>{meta.label}</Tag> : <Tag>{String(v)}</Tag>;
                      },
                    },
                    {
                      title: '处理时间', dataIndex: 'handled_at', key: 'handled_at', width: 170,
                      render: (_: unknown, record: ComplianceItem) => {
                        const time = latestTime(record);
                        return time ? formatDate(time) : '-';
                      },
                    },
                  ]}
                  rowKey="id"
                  loading={rulesLoading}
                  pagination={{ pageSize: 10, showTotal: (t: number) => `共 ${t} 条` }}
                  scroll={{ x: 1100 }}
                  size="middle"
                />
              </Card>
            ),
          },
          {
            key: 'rules',
            label: `规则管理 (${rules.length})`,
            children: (
              <Card size="small">
                <Table<ComplianceRule>
                  dataSource={rules}
                  columns={ruleTableColumns}
                  rowKey="id"
                  loading={rulesLoading}
                  pagination={{ pageSize: 10, showTotal: (t: number) => `共 ${t} 条` }}
                  scroll={{ x: 1100 }}
                  size="middle"
                />
              </Card>
            ),
          },
        ]}
      />

      <Drawer
        title="合规记录详情"
        open={!!detailItem}
        onClose={() => setDetailItem(null)}
        width={480}
      >
        {detailItem ? (
          <Descriptions column={1} size="small" bordered>
            <Descriptions.Item label="记录ID">{detailItem.id}</Descriptions.Item>
            <Descriptions.Item label="状态">
              {STATUS_META[detailItem.status]?.label || detailItem.status}
            </Descriptions.Item>
            <Descriptions.Item label="目标类型">{detailItem.target_type || '-'}</Descriptions.Item>
            <Descriptions.Item label="关联规则">{detailItem.rule_id || '-'}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{detailItem.created_at ? formatDate(detailItem.created_at) : '-'}</Descriptions.Item>
            <Descriptions.Item label="忽略时间">{detailItem.ignored_at ? formatDate(detailItem.ignored_at) : '-'}</Descriptions.Item>
            <Descriptions.Item label="下架时间">{detailItem.taken_down_at ? formatDate(detailItem.taken_down_at) : '-'}</Descriptions.Item>
            <Descriptions.Item label="恢复时间">{detailItem.restored_at ? formatDate(detailItem.restored_at) : '-'}</Descriptions.Item>
          </Descriptions>
        ) : (
          <Empty />
        )}
      </Drawer>

      <Modal
        title={editingRule ? '编辑规则' : '新建规则'}
        open={ruleModalOpen}
        onOk={handleRuleSubmit}
        onCancel={() => setRuleModalOpen(false)}
        confirmLoading={createRule.isPending || updateRule.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="rule_name" label="规则名称" rules={[{ required: true, message: '请输入规则名称' }]}>
            <Input placeholder="如：违禁词检查" maxLength={200} />
          </Form.Item>
          <Form.Item name="rule_type" label="规则类型" rules={[{ required: true }]}>
            <Select options={RULE_TYPE_OPTIONS.map((t) => ({ value: t, label: t }))} />
          </Form.Item>
          <Form.Item name="severity" label="严重程度" rules={[{ required: true }]}>
            <Select options={SEVERITY_OPTIONS.map((s) => ({ value: s, label: SEVERITY_META[s]?.label || s }))} />
          </Form.Item>
          <Form.Item name="category" label="分类" rules={[{ required: true, message: '请输入分类' }]}>
            <Input placeholder="如：通用" maxLength={100} />
          </Form.Item>
          <Form.Item name="applicable_to" label="适用对象" rules={[{ required: true, message: '请至少选择一个适用对象' }]}>
            <Checkbox.Group options={APPLICABLE_TO_OPTIONS} />
          </Form.Item>
          <Form.Item name="enabled" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item
            name="content"
            label="规则内容"
            extra="KEYWORD：逗号分隔关键词；REGEX：正则表达式；其他类型：JSON 配置"
          >
            <Input.TextArea rows={3} placeholder="极限, 最佳, 第一 或 ^\d+$ 或 JSON 配置" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`规则检查历史：${historyRuleId}`}
        open={!!historyRuleId}
        onCancel={() => setHistoryRuleId('')}
        footer={null}
        width={720}
      >
        <Table<ComplianceItem>
          dataSource={historyData?.items || []}
          loading={historyLoading}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 5 }}
          columns={[
            { title: '记录ID', dataIndex: 'id', key: 'id', ellipsis: true },
            {
              title: '状态', dataIndex: 'status', key: 'status', width: 100,
              render: (v: unknown) => STATUS_META[String(v)]?.label || String(v),
            },
            {
              title: '时间', dataIndex: 'created_at', key: 'created_at', width: 170,
              render: (_: unknown, record: ComplianceItem) => {
                const time = latestTime(record);
                return time ? formatDate(time) : '-';
              },
            },
          ]}
        />
      </Modal>
    </PageContainer>
  );
};

export default Compliance;
