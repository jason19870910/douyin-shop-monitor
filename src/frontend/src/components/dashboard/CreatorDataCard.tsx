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
import styles from './CreatorDataCard.module.css';

export interface CreatorTrendData {
  date: string;
  followers: number;
  engagement?: number;
}

interface CreatorDataCardProps {
  totalFollowers: number;
  todayNewFollowers: number;
  avgEngagementRate: number;
  trendData: CreatorTrendData[];
  loading?: boolean;
  className?: string;
}

export const CreatorDataCard = ({
  totalFollowers,
  todayNewFollowers,
  avgEngagementRate,
  trendData,
  loading = false,
  className = '',
}: CreatorDataCardProps) => {
  const chartData = useMemo(
    () =>
      trendData.map((d) => ({
        date: d.date,
        followers: d.followers,
      })),
    [trendData],
  );

  if (loading) {
    return (
      <Card className={`${styles.card} ${className}`}>
        <Skeleton paragraph={{ rows: 8 }} />
      </Card>
    );
  }

  const maxFollowers = Math.max(...chartData.map((d) => d.followers), 1);

  return (
    <Card className={`${styles.card} ${className}`}>
      <div className={styles.header}>
        <h3 className={styles.title}>创作者数据概览</h3>
      </div>

      <div className={styles.metricsGrid}>
        <div className={styles.metricItem}>
          <div className={styles.metricLabel}>粉丝总数</div>
          <div className={styles.metricValue}>{totalFollowers.toLocaleString()}</div>
          <div className={styles.metricTrend} style={{ color: 'var(--color-trend-up)' }}>
            +{todayNewFollowers.toLocaleString()} 今日新增
          </div>
        </div>
        <div className={styles.metricItem}>
          <div className={styles.metricLabel}>平均互动率</div>
          <div className={styles.metricValue}>{(avgEngagementRate * 100).toFixed(2)}%</div>
          <div className={styles.metricTrend}>基于近期内容表现</div>
        </div>
      </div>

      <div className={styles.divider} />

      <div className={styles.chartSection}>
        <h4 className={styles.chartTitle}>粉丝增长趋势 (近7天)</h4>
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
                  value >= 10000 ? `${(value / 10000).toFixed(1)}万` : value.toLocaleString()
                }
                domain={[maxFollowers * 0.95, maxFollowers * 1.05]}
              />
              <Tooltip
                formatter={(value: number) => [value.toLocaleString(), '粉丝数']}
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
                dataKey="followers"
                stroke="var(--color-primary-500)"
                strokeWidth={2}
                dot={{ fill: 'var(--color-primary-500)', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, strokeWidth: 2 }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Card>
  );
};

export default CreatorDataCard;
