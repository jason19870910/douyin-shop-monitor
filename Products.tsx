import React, { useState, useMemo } from 'react';
import { Card, Table, Input, Button, Space, Spin, Tag, message } from 'antd';
import { SearchOutlined, ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import { productApi, type Product, type PaginatedResponse } from '@/api/index';
import { useApi } from '@/hooks/useApi';
import { formatNumber, formatCurrency, formatPercent, formatDateTime } from '@/utils/formatters';
import { PageContainer, PageHeader, TableCard } from '@/components/layout';
import { NormalizedError } from '@/utils/apiClient';
import styles from './Products.module.css';

const Products = () => {
  const [searchText, setSearchText] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const { data, status, error, refetch } = useApi<PaginatedResponse<Product>>(
    () => productApi.getList({ page, size: pageSize, keyword: searchText }),
    [page, pageSize, searchText],
    { retryOnError: true }
  );
  const loading = status === 'loading';

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value);
    setPage(1);
  };

  const handleTableChange = (pagination: { current: number; pageSize: number }) => {
    setPage(pagination.current);
    setPageSize(pagination.pageSize);
  };

  const handleExport = async () => {
    try {
      message.loading('导出中...', 0);
      const result = await productApi.getList({ page: 1, size: 10000, keyword: searchText });
      message.destroy();
      
      const csvContent = [
        ['商品ID', '商品名称', '分类', '价格', '今日销量', '昨日销量', '库存', '转化率', '更新时间'],
        ...(result?.data || []).map(p => [
          p.product_id,
          p.product_name,
          p.category,
          p.price,
          p.sales_today,
          p.sales_yesterday,
          p.inventory,
          p.conversion_rate,
          p.fetched_at,
        ]),
      ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `products_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      message.success('导出成功');
    } catch (err) {
      message.destroy();
      message.error('导出失败');
    }
  };

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
      width: 200,
      ellipsis: true,
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      align: 'right' as const,
      width: 100,
      render: formatCurrency,
    },
    {
      title: '今日销量',
      dataIndex: 'sales_today',
      key: 'sales_today',
      align: 'right' as const,
      width: 100,
      render: formatNumber,
    },
    {
      title: '昨日销量',
      dataIndex: 'sales_yesterday',
      key: 'sales_yesterday',
      align: 'right' as const,
      width: 100,
      render: formatNumber,
    },
    {
      title: '销量变化',
      dataIndex: 'sales_change',
      key: 'sales_change',
      align: 'right' as const,
      width: 100,
      render: (_, record: Product) => {
        const change = record.sales_today - record.sales_yesterday;
        const color = change > 0 ? 'var(--color-trend-up)' : change < 0 ? 'var(--color-trend-down)' : 'var(--color-text-tertiary)';
        const prefix = change > 0 ? '+' : '';
        return <span style={{ color, fontWeight: 500 }}>{prefix}{formatNumber(change)}</span>;
      },
    },
    {
      title: '库存',
      dataIndex: 'inventory',
      key: 'inventory',
      align: 'right' as const,
      width: 100,
      render: (value: number) => (
        <span style={{ color: value <= 10 ? 'var(--color-error-500)' : 'var(--color-text-secondary)', fontWeight: value <= 10 ? 600 : 400 }}>
          {formatNumber(value)}
          {value <= 10 && <Tag style={{ marginLeft: 'var(--spacing-1)', fontSize: 'var(--font-size-xs)' }}>低库存</Tag>}
        </span>
      ),
    },
    {
      title: '转化率',
      dataIndex: 'conversion_rate',
      key: 'conversion_rate',
      align: 'right' as const,
      width: 100,
      render: formatPercent,
    },
    {
      title: '更新时间',
      dataIndex: 'fetched_at',
      key: 'fetched_at',
      width: 160,
      render: formatDateTime,
    },
  ], []);

  const products = data?.data || [];
  const total = data?.total || 0;
  const isMockData = data?.data_source === 'mock';

  return (
    <PageContainer>
      <PageHeader
        title="商品管理"
        filters={
          <Space className={styles.filters}>
            <Input
              placeholder="搜索商品名称..."
              value={searchText}
              onChange={handleSearch}
              prefix={<SearchOutlined />}
              style={{ width: 250 }}
              allowClear
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

      <TableCard<Product>
        dataSource={products}
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
        scroll={{ x: 1300 }}
        size="middle"
      />
    </PageContainer>
  );
};

export default Products;