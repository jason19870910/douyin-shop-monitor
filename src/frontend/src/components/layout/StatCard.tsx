import React from 'react';
import { Card, Statistic } from 'antd';
import styles from './StatCard.module.css';

interface StatCardProps {
  label: string;
  value: string | number;
  trend?: number;
  trendLabel?: string;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  loading?: boolean;
  error?: Error | null;
  subValue?: string;
  subLabel?: string;
  icon?: React.ReactNode;
  className?: string;
}

export const StatCard = ({
  label,
  value,
  trend,
  trendLabel,
  prefix,
  suffix,
  loading = false,
  error = null,
  subValue,
  subLabel,
  icon,
  className = '',
}: StatCardProps) => {
  const trendClass = trend !== undefined && trend !== 0 ? (trend > 0 ? 'up' : 'down') : '';

  return (
    <Card className={`${styles.card} ${trendClass} ${className}`} loading={loading}>
      {error && <div className={styles.error}>{error.message}</div>}
      {icon && <div className={styles.icon}>{icon}</div>}
      <div className={styles.label}>{label}</div>
      <Statistic
        value={value}
        prefix={prefix}
        suffix={suffix}
        valueStyle={{ fontSize: 'var(--font-size-4xl)', fontWeight: 'var(--font-weight-semibold)' }}
      />
      {subValue && (
        <div className={styles.subValue}>
          <span className={styles.subLabel}>{subLabel}:</span>
          <span>{subValue}</span>
        </div>
      )}
      {trend !== undefined && (
        <div className={`${styles.trend} ${trendClass}`}>
          {trend > 0 ? '↑' : trend < 0 ? '↓' : '→'}
          {Math.abs(trend).toFixed(1)}% {trendLabel || 'vs 昨日'}
        </div>
      )}
    </Card>
  );
};

export default StatCard;
