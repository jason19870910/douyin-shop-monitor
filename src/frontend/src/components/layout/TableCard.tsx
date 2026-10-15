import React from 'react';
import { Card, Spin, Alert, Table, TableProps } from 'antd';
import { NormalizedError } from '@/utils/apiClient';
import styles from './TableCard.module.css';

interface TableCardProps<T> {
  title?: React.ReactNode;
  actions?: React.ReactNode;
  dataSource: T[];
  columns: TableProps<T>['columns'];
  rowKey: TableProps<T>['rowKey'];
  loading?: boolean;
  error?: NormalizedError | null;
  pagination?: TableProps<T>['pagination'];
  onTableChange?: TableProps<T>['onChange'];
  onRow?: TableProps<T>['onRow'];
  bordered?: boolean;
  size?: TableProps<T>['size'];
  scroll?: TableProps<T>['scroll'];
  emptyText?: React.ReactNode;
  className?: string;
}

export function TableCard<T>({
  title,
  actions,
  dataSource,
  columns,
  rowKey,
  loading = false,
  error = null,
  pagination,
  onTableChange,
  onRow,
  bordered = false,
  size = 'middle',
  scroll,
  emptyText = '暂无数据',
  className = '',
}: TableCardProps<T>) {
  if (loading && !dataSource.length) {
    return (
      <Card className={`${styles.card} ${className}`} bordered={bordered}>
        <Spin size="large" tip="加载中..." />
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`${styles.card} ${className}`} bordered={bordered}>
        <Alert message="加载失败" description={error.message} type="error" showIcon closable />
      </Card>
    );
  }

  return (
    <Card className={`${styles.card} ${className}`} bordered={bordered}>
      {(title || actions) && (
        <div className={styles.cardHeader}>
          {title && <div className={styles.cardTitle}>{title}</div>}
          {actions && <div className={styles.cardActions}>{actions}</div>}
        </div>
      )}
      <div className={styles.tableWrapper}>
        <Table
          dataSource={dataSource}
          columns={columns}
          rowKey={rowKey}
          pagination={pagination}
          onChange={onTableChange}
          onRow={onRow}
          size={size}
          scroll={scroll}
          loading={loading}
          bordered={bordered}
          locale={{ emptyText }}
        />
      </div>
    </Card>
  );
}

export default TableCard;
