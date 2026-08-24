import React from 'react';
import styles from './PageContainer.module.css';

interface PageContainerProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  background?: 'primary' | 'secondary' | 'tertiary';
}

export const PageContainer = ({
  children,
  className = '',
  padding = 'md',
  background = 'primary',
}: PageContainerProps) => {
  const paddingClass = padding !== 'md' ? ` ${styles[`padding${padding.charAt(0).toUpperCase() + padding.slice(1)}`]}` : '';
  const backgroundClass = background !== 'primary' ? ` ${styles[`bg${background.charAt(0).toUpperCase() + background.slice(1)}`]}` : '';

  return (
    <div className={`${styles.container}${paddingClass}${backgroundClass} ${className}`}>
      {children}
    </div>
  );
};

export default PageContainer;