import { useMemo } from 'react';
import { Card, Skeleton } from 'antd';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import { getStatusLabel, getStatusHexColor } from '@/utils/orderStatus';
import { colors } from '@/theme/tokens';
import styles from './OrderStatusDistribution.module.css';

export interface OrderStatusItem {
  status: string;
  count: number;
  amount: number;
}

interface OrderStatusDistributionProps {
  data: OrderStatusItem[];
  loading?: boolean;
  className?: string;
}

export const OrderStatusDistribution = ({
  data,
  loading = false,
  className = '',
}: OrderStatusDistributionProps) => {
  const chartData = useMemo(() => {
    return data.map((item) => ({
      status: item.status,
      label: getStatusLabel(item.status),
      count: item.count,
      color: getStatusHexColor(item.status),
    }));
  }, [data]);

  const total = useMemo(() => data.reduce((sum, item) => sum + item.count, 0), [data]);

  if (loading) {
    return (
      <Card className={`${styles.card} ${className}`}>
        <Skeleton paragraph={{ rows: 6 }} />
      </Card>
    );
  }

  if (chartData.length === 0) {
    return (
      <Card className={`${styles.card} ${className}`}>
        <div className={styles.emptyState}>
          <p>暂无订单数据</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className={`${styles.card} ${className}`}>
      <div className={styles.header}>
        <h3 className={styles.title}>订单状态分布</h3>
        <span className={styles.total}>共 {total} 单</span>
      </div>
      <div className={styles.chartWrapper}>
        <ResponsiveContainer width="100%" height={240}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              fill={colors.neutral[300]}
              paddingAngle={2}
              dataKey="count"
              nameKey="label"
              label={({ label, percent }) => `${label} ${(percent * 100).toFixed(1)}%`}
              labelLine={false}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number, name: string) => [value, name]}
              labelFormatter={(label: string) => `状态: ${label}`}
            />
            <Legend
              layout="vertical"
              align="right"
              verticalAlign="middle"
              iconType="circle"
              formatter={(label: string) => {
                const item = chartData.find((d) => d.label === label);
                return `${label} ${item ? item.count : 0} 单`;
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className={styles.legend}>
        {chartData.map((item, index) => (
          <div key={index} className={styles.legendItem}>
            <span className={styles.legendColor} style={{ backgroundColor: item.color }} />
            <span className={styles.legendLabel}>
              {item.label} {item.count} 单 ({((item.count / total) * 100).toFixed(1)}%)
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
};

export default OrderStatusDistribution;