import { useMemo } from 'react';
import { formatNumber, formatCurrency, formatDate } from '@/utils/formatters';
import { orderApi, type Order } from '@/api/index';
import { DataTable, type DataTableColumn } from '@/components/common';
import { normalizeOrderStatus, getStatusLabel, getStatusColor } from '@/utils/orderStatus';
import { queryKeys } from '@/hooks';

const Orders = () => {
  const columns = useMemo<DataTableColumn<Order>[]>(() => [
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
      render: (_value: unknown, record: Order) => (record.product_name || record.product || record.name || '-') as React.ReactNode,
    },
    {
      title: '创作者',
      dataIndex: 'creator_name',
      key: 'creator_name',
      width: 150,
      render: (_value: unknown, record: Order) => (record.creator_name || record.buyer_name || record.buyer_nickname || '-') as React.ReactNode,
    },
    {
      title: '金额',
      dataIndex: 'pay_amount',
      key: 'amount',
      align: 'right',
      width: 120,
      render: (_value: unknown, record: Order) => formatCurrency((record.pay_amount ?? record.total_price ?? 0) as number | null | undefined),
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      align: 'right',
      width: 80,
      render: (value: unknown) => formatNumber(value as number | null | undefined),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      align: 'center',
      width: 100,
      render: (status: unknown) => {
        const statusStr = typeof status === 'string' ? status : '';
        const normalizedStatus = normalizeOrderStatus(statusStr);
        return (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '2px 8px',
              borderRadius: 4,
              background: `${getStatusColor(normalizedStatus)}15`,
              color: getStatusColor(normalizedStatus),
              fontWeight: 500,
              fontSize: 12,
            }}
          >
            {getStatusLabel(normalizedStatus)}
          </span>
        );
      },
    },
    {
      title: '下单时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 180,
      render: (value: unknown) => formatDate(value as string | null | undefined),
    },
    {
      title: '更新时间',
      dataIndex: 'update_time',
      key: 'update_time',
      width: 180,
      render: (value: unknown) => formatDate(value as string | null | undefined),
    },
  ], []);

  return (
    <DataTable<Order>
      title="订单管理"
      queryKey={queryKeys.orders.list({})}
      queryFn={(params) => orderApi.getList(params) as Promise<{ items: Order[]; total: number }>}
      columns={columns}
      rowKey="order_id"
      search={{ placeholder: '搜索商品/创作者...' }}
      filters={[
        {
          key: 'start_date',
          label: '开始日期',
          type: 'dateRange',
          placeholder: '开始日期 - 结束日期',
          style: { width: 300 },
        },
        {
          key: 'status',
          label: '订单状态',
          type: 'select',
          options: [
            { value: 'completed', label: '已完成' },
            { value: 'pending', label: '待处理' },
            { value: 'shipped', label: '已发货' },
            { value: 'cancelled', label: '已取消' },
            { value: 'refunded', label: '已退款' },
          ],
          style: { width: 140 },
        },
      ]}
      exportConfig={{
        filenamePrefix: 'orders',
        columns: [
          { key: 'order_id', label: '订单ID' },
          { key: 'product_name', label: '商品名称', render: (r: Order) => r.product_name || r.product || r.name },
          { key: 'creator_name', label: '创作者', render: (r: Order) => r.creator_name || r.buyer_name || r.buyer_nickname },
          { key: 'pay_amount', label: '金额', render: (r: Order) => (r.pay_amount ?? r.total_price ?? 0) },
          { key: 'quantity', label: '数量' },
          { key: 'status', label: '状态' },
          { key: 'create_time', label: '下单时间' },
          { key: 'update_time', label: '更新时间' },
        ],
      }}
    />
  );
};

export default Orders;