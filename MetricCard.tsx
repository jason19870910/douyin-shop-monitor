import React from 'react';
import { Card, Typography, Space, Skeleton } from 'antd';
import styles from './MetricCard.module.css';

const { Title, Text } = Typography;

interface MetricCardProps {
  label: string;
  value: string | number;
  trend?: number;
  trendLabel?: string;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  icon?: React.ReactNode;
  loading?: boolean;
  className?: string;
}

export const MetricCard = ({
  label,
  value,
  trend,
  trendLabel = 'vs 昨日',
  prefix,
  suffix,
  icon,
  loading = false,
  className = '',
}: MetricCardProps) => {
  if (loading) {
    return (
      <Card className={`${styles.card} ${className}`}>
        <Skeleton paragraph={{ rows: 3 }} />
      </Card>
    );
  }

  const trendClass = trend !== undefined && trend !== 0
    ? trend > 0
      ? 'up'
      : 'down'
    : '';

  return (
    <Card className={`${styles.card} ${className}`}>
      <div className={styles.header}>
        <div className={styles.label}>
          {icon && <span className={styles.icon}>{icon}</span>}
          <Title level={5} className={styles.labelText}>{label}</Title>
        </div>
      </div>
      <div className={styles.valueWrapper}>
        <Text className={styles.value} strong>
          {prefix}{value}{suffix}
        </Text>
      </div>
      {trend !== undefined && (
        <div className={`${styles.trend} ${trendClass}`}>
          {trend > 0 ? (
            <span className={styles.trendUp}>↑ {Math.abs(trend).toFixed(1)}%</span>
          ) : trend < 0 ? (
            <span className={styles.trendDown}>↓ {Math.abs(trend).toFixed(1)}%</span>
          ) : (
            <span className={styles.trendFlat}>→ 0.0%</span>
          )}
          <span className={styles.trendLabel}>{trendLabel}</span>
        </div>
      )}
    </Card>
  );
};

export default MetricCard;