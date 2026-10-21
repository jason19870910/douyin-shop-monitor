import { useState } from 'react';
import {
  Card,
  Button,
  Tag,
  Select,
  Modal,
  Descriptions,
  Popconfirm,
  message,
  Empty,
  Tooltip,
  Space,
} from 'antd';
import {
  ReloadOutlined,
  DeleteOutlined,
  BellOutlined,
  WarningOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { alertApi, type AlertHistoryItem } from '@/api/index';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageContainer, PageHeader, TableCard } from '@/components/layout';
import { formatDateTime } from '@/utils/formatters';
import type { NormalizedError } from '@/utils/apiClient';

const ALERT_TYPE_LABELS: Record<string, string> = {
  sales_drop: '销量下跌',
  low_inventory: '库存不足',
  conversion_drop: '转化率下跌',
  video_view_drop: '播放量下跌',
  video_like_drop: '点赞数下跌',
  creator_follower_drop: '粉丝流失',
  dian_product_sales_drop: '商品销量下跌',
  order_refund_rate: '订单退款率',
  dian_compliance_risk: '合规风险',
};

const ALERT_TYPE_COLORS: Record<string, string> = {
  sales_drop: 'red',
  low_inventory: 'orange',
  conversion_drop: 'volcano',
  video_view_drop: 'blue',
  video_like_drop: 'geekblue',
  creator_follower_drop: 'purple',
  dian_product_sales_drop: 'magenta',
  order_refund_rate: 'gold',
  dian_compliance_risk: 'lime',
};

const AlertHistory = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [typeFilter, setTypeFilter] = useState<string | undefined>(undefined);
  const [detailAlert, setDetailAlert] = useState<AlertHistoryItem | null>(null);
  const [clearing, setClearing] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['alerts', 'history', { page, pageSize, typeFilter }],
    queryFn: () => alertApi.getHistory({ limit: pageSize, offset: (page - 1) * pageSize, type: typeFilter }) as Promise<{ items: AlertHistoryItem[]; total: number }>,
    staleTime: 1000 * 60 * 2,
    gcTime: 1000 * 60 * 10,
    retry: 2,
  });

  const { data: statsData } = useQuery({
    queryKey: ['alerts', 'stats'],
    queryFn: () => alertApi.getStats() as Promise<{ total: number; by_type: Record<string, number> }>,
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });

  const clearHistoryMutation = useMutation({
    mutationFn: () => alertApi.clearHistory() as Promise<{ cleared: number }>,
    onSuccess: (result) => {
      const clearedCount = typeof result === 'number' ? result : (result?.cleared ?? 0);
      message.success(`已清除 ${clearedCount} 条告警记录`);
      queryClient.invalidateQueries({ queryKey: ['alerts', 'history'] });
      queryClient.invalidateQueries({ queryKey: ['alerts', 'stats'] });
    },
    onError: (err) => {
      message.error('清除失败: ' + (err as Error).message);
    },
    onSettled: () => {
      setClearing(false);
    },
  });

  const list: AlertHistoryItem[] = data?.items || [];
  const total = data?.total || 0;

  const handleClear = async () => {
    setClearing(true);
    clearHistoryMutation.mutate();
  };

  const handleRefetch = () => refetch();

  const columns = [
    {
      title: '告警类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (value: unknown) => {
        const type = value as string;
        return (
          <Tag color={ALERT_TYPE_COLORS[type] || 'default'} icon={<WarningOutlined />}>
            {ALERT_TYPE_LABELS[type] || type}
          </Tag>
        );
      },
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 200,
      ellipsis: { showTitle: false },
      render: (value: unknown) => {
        const name = value as string;
        return (
          <Tooltip title={name}>
            <span>{name || '-'}</span>
          </Tooltip>
        );
      },
    },
    {
      title: '告警详情',
      dataIndex: 'message',
      key: 'message',
      width: 200,
      ellipsis: { showTitle: false },
      render: (value: unknown) => {
        const msg = value as string;
        return (
          <Tooltip title={msg}>
            <span>{msg}</span>
          </Tooltip>
        );
      },
    },
    {
      title: '下降幅度',
      dataIndex: 'drop_rate',
      key: 'drop_rate',
      width: 100,
      render: (value: unknown) => {
        const rate = value as number | undefined;
        return rate !== undefined ? (
          <span style={{ color: 'var(--color-error-500)', fontWeight: 600 }}>
            {(rate * 100).toFixed(1)}%
          </span>
        ) : (
          '-'
        );
      },
    },
    {
      title: '当前值',
      dataIndex: 'inventory',
      key: 'inventory',
      width: 100,
      render: (value: unknown, record: AlertHistoryItem) => {
        const val = value as number | undefined;
        if (val !== undefined) return `${val}`;
        if (record.drop_rate !== undefined) {
          return `${(record.drop_rate * 100).toFixed(1)}%`;
        }
        return '-';
      },
    },
    {
      title: '触发时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (value: unknown) => formatDateTime(value as string),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_value: unknown, record: AlertHistoryItem) => (
        <Button type="link" size="small" onClick={() => setDetailAlert(record)}>
          详情
        </Button>
      ),
    },
  ];

  const handleTableChange = (page: number, pageSize: number) => {
    setPage(page);
    setPageSize(pageSize);
  };

  return (
    <PageContainer>
      <PageHeader
        title={
          <>
            <BellOutlined style={{ marginRight: 'var(--spacing-2)' }} /> 告警历史
          </>
        }
        actions={
          <Space>
            <Select
              allowClear
              placeholder="按类型筛选"
              style={{ width: 150 }}
              value={typeFilter}
              onChange={(val) => {
                setTypeFilter(val);
                setPage(1);
              }}
              options={[
                { label: '销量下跌', value: 'sales_drop' },
                { label: '库存不足', value: 'low_inventory' },
                { label: '转化率下跌', value: 'conversion_drop' },
                { label: '播放量下跌', value: 'video_view_drop' },
                { label: '点赞数下跌', value: 'video_like_drop' },
                { label: '粉丝流失', value: 'creator_follower_drop' },
                { label: '商品销量下跌', value: 'dian_product_sales_drop' },
                { label: '订单退款率', value: 'order_refund_rate' },
                { label: '合规风险', value: 'dian_compliance_risk' },
              ]}
            />
            <Button icon={<ReloadOutlined />} onClick={handleRefetch} loading={isLoading}>
              刷新
            </Button>
            <Popconfirm
              title="确定清除所有告警历史吗？"
              description="此操作不可恢复"
              icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
              onConfirm={handleClear}
              disabled={total === 0}
            >
              <Button
                danger
                icon={<DeleteOutlined />}
                loading={clearing}
                disabled={total === 0}
              >
                清除全部
              </Button>
            </Popconfirm>
          </Space>
        }
      />

      {statsData && total > 0 && (
        <Card style={{ marginBottom: 'var(--spacing-4)' }} size="small">
          <Space size="large">
            <span>
              总告警数: <strong>{statsData.total}</strong>
            </span>
            {Object.entries(statsData.by_type).map(([type, count]) => (
              <Tag key={type} color={ALERT_TYPE_COLORS[type] || 'default'}>
                {ALERT_TYPE_LABELS[type] || type}: {count}
              </Tag>
            ))}
          </Space>
        </Card>
      )}

      <TableCard<AlertHistoryItem>
        rowKey={(record) => `${record.timestamp}-${record.product_id}-${record.type}`}
        columns={columns}
        dataSource={list}
        loading={isLoading}
        error={isError ? error as unknown as NormalizedError : null}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (t) => `共 ${t} 条告警`,
          onChange: handleTableChange,
        }}
        emptyText={<Empty description="暂无告警记录" />}
        scroll={{ x: 900 }}
      />

      <Modal
        title="告警详情"
        open={!!detailAlert}
        onCancel={() => setDetailAlert(null)}
        footer={[
          <Button key="close" onClick={() => setDetailAlert(null)}>
            关闭
          </Button>,
        ]}
      >
        {detailAlert && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="告警类型">
              <Tag color={ALERT_TYPE_COLORS[detailAlert.type] || 'default'}>
                {ALERT_TYPE_LABELS[detailAlert.type] || detailAlert.type}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="商品ID">
              {detailAlert.product_id || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="商品名称">
              {detailAlert.product_name || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="告警消息">
              {detailAlert.message}
            </Descriptions.Item>
            {detailAlert.drop_rate !== undefined && (
              <Descriptions.Item label="下降幅度">
                {(detailAlert.drop_rate * 100).toFixed(2)}%
              </Descriptions.Item>
            )}
            {detailAlert.inventory !== undefined && (
              <Descriptions.Item label="当前库存">
                {detailAlert.inventory}
              </Descriptions.Item>
            )}
            {detailAlert.threshold !== undefined && (
              <Descriptions.Item label="触发阈值">
                {typeof detailAlert.threshold === 'number' && detailAlert.threshold < 1
                  ? `${(detailAlert.threshold * 100).toFixed(1)}%`
                  : detailAlert.threshold}
              </Descriptions.Item>
            )}
            <Descriptions.Item label="触发时间">
              {formatDateTime(detailAlert.timestamp)}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </PageContainer>
  );
};

export default AlertHistory;