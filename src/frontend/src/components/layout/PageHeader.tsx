import type { ReactNode } from 'react';
import styles from './PageHeader.module.css';

interface PageHeaderProps {
  title: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  filters?: ReactNode;
  className?: string;
}

export const PageHeader = ({
  title,
  subtitle,
  actions,
  filters,
  className = '',
}: PageHeaderProps) => {
  return (
    <div className={`${styles.container} ${className}`}>
      <div className={styles.headerMain}>
        <div className={styles.titleArea}>
          <h1 className={styles.title}>{title}</h1>
          {subtitle && <div className={styles.subtitle}>{subtitle}</div>}
        </div>
        {actions && <div className={styles.actions}>{actions}</div>}
      </div>
      {filters && <div className={styles.filters}>{filters}</div>}
    </div>
  );
};

export default PageHeader;
