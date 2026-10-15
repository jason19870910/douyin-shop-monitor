import { useMemo } from 'react';
import { Card, Skeleton } from 'antd';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import styles from './OrderTrendMiniChart.module.css';

interface OrderTrendData {
  date: string;
  count?: number;
  sales?: number;
}

interface OrderTrendMiniChartProps {
  data: OrderTrendData[];
  title?: string;
  color?: string;
  loading?: boolean;
  className?: string;
}

export const OrderTrendMiniChart = ({
  data,
  title = '销售趋势 (近7天)',
  color = 'var(--color-primary-500)',
  loading = false,
  className = '',
}: OrderTrendMiniChartProps) => {
  const chartData = useMemo(
    () =>
      data.map((d) => ({
        date: d.date,
        count: d.count ?? d.sales ?? 0,
      })),
    [data],
  );

  const maxCount = Math.max(...chartData.map((d) => d.count), 1);

  if (loading) {
    return (
      <Card className={`${styles.card} ${className}`}>
        <Skeleton paragraph={{ rows: 5 }} />
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card className={`${styles.card} ${className}`}>
        <div className={styles.emptyState}>暂无销售趋势数据</div>
      </Card>
    );
  }

  return (
    <Card className={`${styles.card} ${className}`}>
      <div className={styles.header}>
        <h3 className={styles.title}>{title}</h3>
      </div>
      <div className={styles.chartWrapper}>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--color-border-light)"
              vertical={false}
            />
            <XAxis
              dataKey="date"
              stroke="var(--color-text-tertiary)"
              fontSize={11}
              tick={{ fill: 'var(--color-text-tertiary)' }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="var(--color-text-tertiary)"
              fontSize={11}
              tick={{ fill: 'var(--color-text-tertiary)' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value: number) =>
                value >= 10000 ? `${(value / 10000).toFixed(1)}万` : value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value.toString()
              }
              domain={[0, maxCount * 1.2]}
            />
            <Tooltip
              formatter={(value: number) => [value, '销售额']}
              labelFormatter={(date: string) => `日期: ${date}`}
              contentStyle={{
                backgroundColor: 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border-light)',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-lg)',
              }}
            />
            <Line
              type="monotone"
              dataKey="count"
              stroke={color}
              strokeWidth={2}
              dot={{ fill: color, strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, strokeWidth: 2 }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

export default OrderTrendMiniChart;
