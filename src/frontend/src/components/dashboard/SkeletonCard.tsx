import { Card, Skeleton } from 'antd';
import styles from './SkeletonCard.module.css';

interface SkeletonCardProps {
  variant?: 'metric' | 'chart' | 'table' | 'default';
  className?: string;
}

export const SkeletonCard = ({ variant = 'default', className = '' }: SkeletonCardProps) => {
  const renderSkeleton = () => {
    switch (variant) {
      case 'metric':
        return (
          <>
            <Skeleton paragraph={{ rows: 1, width: '60%' }} />
            <Skeleton
              paragraph={{ rows: 1, width: '100%' }}
              style={{ marginTop: 'var(--spacing-3)' }}
            />
            <Skeleton
              paragraph={{ rows: 1, width: '40%' }}
              style={{ marginTop: 'var(--spacing-3)' }}
            />
          </>
        );
      case 'chart':
        return (
          <>
            <Skeleton paragraph={{ rows: 1, width: '40%' }} />
            <Skeleton
              active
              style={{
                marginTop: 'var(--spacing-4)',
                height: '200px',
                width: '100%',
                borderRadius: 'var(--radius-md)',
              }}
            />
          </>
        );
      case 'table':
        return (
          <>
            <Skeleton paragraph={{ rows: 1, width: '30%' }} />
            <Skeleton
              active
              style={{
                marginTop: 'var(--spacing-4)',
                height: '280px',
                width: '100%',
                borderRadius: 'var(--radius-md)',
              }}
            />
          </>
        );
      default:
        return <Skeleton active paragraph={{ rows: 4, width: '100%' }} />;
    }
  };

  return <Card className={`${styles.card} ${className}`}>{renderSkeleton()}</Card>;
};

export default SkeletonCard;
