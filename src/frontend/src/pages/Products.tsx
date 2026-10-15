import { useMemo, useState } from 'react';
import dayjs from 'dayjs';
import { Drawer, Descriptions, Spin, Empty, DatePicker, Space } from 'antd';
import { formatNumber, formatCurrency, formatPercent, formatDate } from '@/utils/formatters';
import { productApi, type Product, type ProductListParams } from '@/api/index';
import { DataTable, type DataTableColumn } from '@/components/common';
import { queryKeys } from '@/hooks';
import { useProductDetail } from '@/hooks/useQueries';

const productImageStyle = { width: 48, height: 48, objectFit: 'cover' as const, borderRadius: 4 };

const Products = () => {
  const [dataSource, _setDataSource] = useState<'cache' | 'external'>('cache');
  const [detailDrawerOpen, setDetailDrawerOpen] = useState(false);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null]>([null, null]);
  const { data: productDetail, isLoading: detailLoading } = useProductDetail(selectedProductId || '', { enabled: !!selectedProductId });
  const product = productDetail as Product | undefined;

  // Handle date range change
  const handleDateRangeChange = (dates: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null) => {
    if (dates) {
      setDateRange(dates);
    } else {
      setDateRange([null, null]);
    }
  };

  const columns = useMemo<DataTableColumn<Product>[]>(() => [
    {
      title: '商品ID',
      dataIndex: 'product_id',
      key: 'product_id',
      width: 120,
    },
    {
      title: '封面',
      dataIndex: 'img',
      key: 'img',
      width: 80,
      render: (_value: unknown, record: Product): React.ReactNode => {
        const imgUrl = (record as Record<string, unknown>).img as string | undefined;
        if (!imgUrl) return null;
        return (
          <img
            src={imgUrl}
            alt={record.product_name || '商品封面'}
            loading="lazy"
            style={productImageStyle}
            onError={(e) => {
              e.currentTarget.style.display = 'none';
            }}
          />
        );
      },
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 240,
      ellipsis: true,
      render: (_value: unknown, record: Product): React.ReactNode => (record.product_name || record.name || '-') as React.ReactNode,
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
      align: 'right',
      width: 120,
      render: (_value: unknown, record: Product) => {
        // API 返回价格单位为分，需除以 100 转为元
        const priceFen = record.price ?? record.discount_price ?? record.market_price ?? 0;
        return formatCurrency(priceFen / 100);
      },
    },
    {
      title: '今日销量',
      dataIndex: 'sales_today',
      key: 'sales_today',
      align: 'right',
      width: 100,
      render: (value: unknown) => formatNumber(value as number | null | undefined),
    },
    {
      title: '昨日销量',
      dataIndex: 'sales_yesterday',
      key: 'sales_yesterday',
      align: 'right',
      width: 100,
      render: (value: unknown) => formatNumber(value as number | null | undefined),
    },
    {
      title: '销量变化',
      dataIndex: 'sales_change',
      key: 'sales_change',
      align: 'right',
      width: 100,
      render: (_value: unknown, record: Product) => {
        const change = record.sales_today - record.sales_yesterday;
        const color =
          change > 0
            ? 'var(--color-trend-up)'
            : change < 0
            ? 'var(--color-trend-down)'
            : 'var(--color-text-tertiary)';
        const prefix = change > 0 ? '+' : '';
        return (
          <span style={{ color, fontWeight: 500 }}>
            {prefix}
            {formatNumber(change)}
          </span>
        );
      },
    },
    {
      title: '库存',
      dataIndex: 'inventory',
      key: 'inventory',
      align: 'right',
      width: 100,
      render: (value: unknown) => {
        const num = value as number;
        return (
          <span
            style={{
              color: num <= 10 ? 'var(--color-error-500)' : 'var(--color-text-secondary)',
              fontWeight: num <= 10 ? 600 : 400,
            }}
          >
            {formatNumber(num)}
            {num <= 10 && (
              <span style={{ marginLeft: 8, padding: '2px 6px', borderRadius: 4, background: 'var(--color-error-500)', color: 'var(--color-text-inverted)', fontSize: 11 }}>
                低库存
              </span>
            )}
          </span>
        );
      },
    },
    {
      title: '转化率',
      dataIndex: 'conversion_rate',
      key: 'conversion_rate',
      align: 'right',
      width: 100,
      render: (value: unknown) => formatPercent(value as number | null | undefined),
    },
    {
      title: '更新时间',
      dataIndex: 'fetched_at',
      key: 'fetched_at',
      width: 160,
      render: (value: unknown) => formatDate(value as string | null | undefined),
    },
    {
      title: '操作',
      dataIndex: 'actions',
      key: 'actions',
      width: 80,
      render: (_: unknown, record: Product) => (
        <span onClick={() => { setSelectedProductId(record.product_id); setDetailDrawerOpen(true); }} style={{ cursor: 'pointer', color: 'var(--color-primary-500)' }}>详情</span>
      ),
    },
  ], []);

  // 根据数据源动态选择 API
  const queryFn = (params: Record<string, unknown>) => {
    // Add date filter parameters
    const dateParams: ProductListParams = {
      ...params,
      start_date: dateRange[0] ? dateRange[0].format('YYYY-MM-DD') : undefined,
      end_date: dateRange[1] ? dateRange[1].format('YYYY-MM-DD') : undefined,
    };
    
    if (dataSource === 'external') {
      return productApi.getExternal(dateParams) as Promise<{ items: Product[]; total: number }>;
    }
    return productApi.getList(dateParams) as Promise<{ items: Product[]; total: number }>;
  };

  const fullQueryKey = [...queryKeys.products.list({}), dataSource];

  // Date range picker for extraActions
  const datePickerExtraActions = (
    <Space>
      <DatePicker.RangePicker
        value={dateRange}
        onChange={handleDateRangeChange}
        placeholder={['开始日期', '结束日期']}
        format="YYYY-MM-DD"
        style={{ width: 300 }}
        allowClear
      />
    </Space>
  );

  return (
    <>
      <DataTable<Product>
        title="商品管理"
        queryKey={fullQueryKey}
        queryFn={queryFn}
        columns={columns}
        rowKey="product_id"
        search={{ placeholder: '搜索商品名称...' }}
        exportConfig={{
          filenamePrefix: 'products',
          columns: [
            { key: 'product_id', label: '商品ID' },
            { key: 'product_name', label: '商品名称' },
            { key: 'category', label: '分类' },
            { key: 'price', label: '价格', render: (record: Product) => (record.price ?? 0) / 100 },
            { key: 'market_price', label: '原价', render: (record: Product) => (record.market_price ?? 0) / 100 },
            { key: 'discount_price', label: '折扣价', render: (record: Product) => (record.discount_price ?? 0) / 100 },
            { key: 'sales_today', label: '今日销量' },
            { key: 'sales_yesterday', label: '昨日销量' },
            { key: 'inventory', label: '库存' },
            { key: 'conversion_rate', label: '转化率' },
            { key: 'fetched_at', label: '更新时间' },
            { key: 'product_url', label: '商品链接' },
            { key: 'img', label: '封面图' },
          ],
        }}
        showDataSourceSwitch={true}
        extraActions={datePickerExtraActions}
      ></DataTable>
      <Drawer
      title="商品详情"
      width={720}
      open={detailDrawerOpen}
      onClose={() => { setDetailDrawerOpen(false); setSelectedProductId(null); }}
    >
      {detailLoading ? (
        <Spin size="large" tip="加载详情..." />
      ) : product ? (
        <Descriptions column={2} size="small" bordered>
          <Descriptions.Item label="商品ID">{product?.product_id}</Descriptions.Item>
          <Descriptions.Item label="商品名称">{product?.product_name}</Descriptions.Item>
          <Descriptions.Item label="分类">{product?.category}</Descriptions.Item>
          <Descriptions.Item label="价格">{formatCurrency((product?.price ?? 0) / 100)}</Descriptions.Item>
          <Descriptions.Item label="原价">{formatCurrency((product?.market_price ?? 0) / 100)}</Descriptions.Item>
          <Descriptions.Item label="折扣价">{formatCurrency((product?.discount_price ?? 0) / 100)}</Descriptions.Item>
          <Descriptions.Item label="今日销量">{formatNumber(product?.sales_today)}</Descriptions.Item>
          <Descriptions.Item label="昨日销量">{formatNumber(product?.sales_yesterday)}</Descriptions.Item>
          <Descriptions.Item label="库存">{formatNumber(product?.inventory)}</Descriptions.Item>
          <Descriptions.Item label="转化率">{formatPercent(product?.conversion_rate)}</Descriptions.Item>
          <Descriptions.Item label="商品链接"><a href={product?.product_url} target="_blank" rel="noopener noreferrer">{product?.product_url}</a></Descriptions.Item>
          <Descriptions.Item label="更新时间">{formatDate(product?.fetched_at)}</Descriptions.Item>
        </Descriptions>
      ) : (
        <Empty description="无详情数据" />
      )}
    </Drawer>
    </>
  );
};

export default Products;