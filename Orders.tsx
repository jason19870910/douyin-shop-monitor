import React, { useState, useMemo } from 'react';
import dayjs from 'dayjs';
import { Card, Table, Input, Button, Space, Spin, DatePicker, message, Tag, Select } from 'antd';
import { SearchOutlined, ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import { orderApi, type Order, type OrderListResponse } from '@/api/index';
import { useApi } from '@/hooks/useApi';
import { formatNumber, formatCurrency, formatDateTime } from '@/utils/formatters';
import { PageContainer, PageHeader, TableCard } from '@/components/layout';
import { NormalizedError } from '@/utils/apiClient';
import styles from './Orders.module.css';

const { RangePicker } = DatePicker;
type DateRangeValue = [dayjs.Dayjs, dayjs.Dayjs] | null;

const Orders = () => {
  const [searchText, setSearchText] = useState('');
  const [dateRange, setDateRange] = useState<DateRangeValue>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState('');

  const { data, status, error, refetch } = useApi<OrderListResponse>(
    () => orderApi.getList({ 
      page, 
      size: pageSize, 
      keyword: searchText,
      start_date: dateRange?.[0]?.format('YYYY-MM-DD'),
      end_date: dateRange?.[1]?.format('YYYY-MM-DD'),
      status: statusFilter,
    }),
    [page, pageSize, searchText, dateRange, statusFilter],
    { retryOnError: true }
  );
  const loading = status === 'loading';

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value);
    setPage(1);
  };

  const handleDateChange = (dates: DateRangeValue) => {
    setDateRange(dates);
    setPage(1);
  };

  const handleStatusChange = (value: string) => {
    setStatusFilter(value);
    setPage(1);
  };

  const handleTableChange = (pagination: { current: number; pageSize: number }) => {
    setPage(pagination.current);
    setPageSize(pagination.pageSize);
  };

  const handleExport = async () => {
    try {
      message.loading('导出中...', 0);
      const result = await orderApi.getList({ 
        page: 1, 
        size: 10000, 
        keyword: searchText,
        start_date: dateRange?.[0]?.format('YYYY-MM-DD'),
        end_date: dateRange?.[1]?.format('YYYY-MM-DD'),
        status: statusFilter,
      });
      message.destroy();
      
      const csvContent = [
        ['订单ID', '商品名称', '创作者', '金额', '数量', '状态', '下单时间', '更新时间'],
        ...(result?.list || []).map(o => [
          o.order_id,
          o.product_name,
          o.creator_name,
          o.amount,
          o.quantity,
          o.status,
          o.create_time,
          o.update_time,
        ]),
      ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `orders_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      message.success('导出成功');
    } catch (err) {
      message.destroy();
      message.error('导出失败');
    }
  };

  const columns = useMemo(() => [
    {
      title: '订单ID',
      dataIndex: 'order_id',
      key: 'order_id',
      width: 150,
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 200,
      ellipsis: true,
    },
    {
      title: '创作者',
      dataIndex: 'creator_name',
      key: 'creator_name',
      width: 150,
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      align: 'right' as const,
      width: 120,
      render: formatCurrency,
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      align: 'right' as const,
      width: 80,
      render: formatNumber,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      align: 'center' as const,
      render: (status: string) => {
        const statusMap: Record<string, { color: string; text: string }> = {
          'completed': { color: 'green', text: '已完成' },
          'pending': { color: 'orange', text: '待处理' },
          'cancelled': { color: 'red', text: '已取消' },
          'refunded': { color: 'blue', text: '已退款' },
        };
        const s = statusMap[status] || { color: 'default', text: status };
        return <Tag color={s.color}>{s.text}</Tag>;
      },
    },
    {
      title: '下单时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 180,
      render: formatDateTime,
    },
    {
      title: '更新时间',
      dataIndex: 'update_time',
      key: 'update_time',
      width: 180,
      render: formatDateTime,
    },
  ], []);

  const orders = data?.list || [];
  const total = data?.total || 0;
  const isMockData = data?.data_source === 'mock';

  return (
    <PageContainer>
      <PageHeader
        title="订单管理"
        filters={
          <Space wrap className={styles.filters}>
            <Input
              placeholder="搜索商品/创作者..."
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
              placeholder="订单状态"
              value={statusFilter}
              onChange={handleStatusChange}
              allowClear
              style={{ width: 140 }}
              options={[
                { value: 'completed', label: '已完成' },
                { value: 'pending', label: '待处理' },
                { value: 'cancelled', label: '已取消' },
                { value: 'refunded', label: '已退款' },
              ]}
            />
          </Space>
        }
        actions={
          <Space>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>导出 CSV</Button>
            <Button icon={<ReloadOutlined />} onClick={refetch} loading={loading}>刷新</Button>
            {isMockData && <Tag color="orange">⚠ 模拟数据</Tag>}
          </Space>
        }
      />

      <TableCard<Order>
        dataSource={orders}
        columns={columns}
        rowKey="order_id"
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
        scroll={{ x: 1200 }}
        size="middle"
      />
    </PageContainer>
  );
};

export default Orders;