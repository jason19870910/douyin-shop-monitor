import { useState, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { TablePaginationConfig, SorterResult, FilterValue, TableCurrentDataSource } from 'antd/es/table/interface';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import { TableCard } from '@/components/layout/TableCard';
import type { NormalizedError } from '@/utils/apiClient';
import type { PaginatedResponse } from '@/api';

export interface DataTableColumn<T> {
  title: string;
  dataIndex: string;
  key: string;
  width?: number;
  align?: 'left' | 'center' | 'right';
  render?: (value: unknown, record: T, index: number) => React.ReactNode;
  ellipsis?: boolean;
  sorter?: boolean;
  filterDropdown?: React.ReactNode;
  filters?: Array<{ text: string; value: string }>;
  onFilter?: (value: string, record: T) => boolean;
}

export interface DataTableProps<T> {
  title: string;
  queryKey: readonly unknown[];
  queryFn: (params: Record<string, unknown>) => Promise<PaginatedResponse<T>>;
  columns: DataTableColumn<T>[];
  rowKey: string;
  search?: {
    placeholder?: string;
    onSearch?: (value: string) => void;
    initialValue?: string;
  };
  filters?: Array<{
    key: string;
    label: string;
    type: 'select' | 'dateRange' | 'input';
    options?: Array<{ value: string; label: string }>;
    placeholder?: string;
    style?: React.CSSProperties;
  }>;
  extraActions?: React.ReactNode;
  pageSizeOptions?: number[];
  defaultPageSize?: number;
  scrollX?: number;
  size?: 'small' | 'middle' | 'large';
  bordered?: boolean;
  exportConfig?: {
    filenamePrefix: string;
    columns: Array<{ key: string; label: string; render?: (record: T) => unknown }>;
  };
  onRowClick?: (record: T) => void;
  transformResponse?: (data: PaginatedResponse<T>) => PaginatedResponse<T>;
  queryOptions?: {
    staleTime?: number;
    gcTime?: number;
    retry?: number;
    refetchOnWindowFocus?: boolean;
    refetchInterval?: number;
  };
  showDataSourceSwitch?: boolean;
}

export function DataTable<T extends Record<string, unknown>>({
  title: _title,
  queryKey,
  queryFn,
  columns,
  rowKey,
  search,
  filters: _filters = [],
  extraActions: _extraActions,
  pageSizeOptions = [10, 20, 50, 100],
  defaultPageSize = 20,
  scrollX = 1200,
  size = 'middle',
  bordered = false,
  exportConfig: _exportConfig,
  onRowClick,
  transformResponse,
  queryOptions,
  showDataSourceSwitch: _showDataSourceSwitch = false,
}: DataTableProps<T>) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(defaultPageSize);
  const [searchText] = useState(search?.initialValue || '');
  const [filterValues] = useState<Record<string, unknown>>({});

  const buildParams = useCallback(() => {
    const params: Record<string, unknown> = {
      page,
      size: pageSize,
    };
    if (searchText) params.keyword = searchText;
    Object.entries(filterValues).forEach(([key, value]) => {
      if (value !== '' && value !== null && value !== undefined) {
        params[key] = value;
      }
    });
    return params;
  }, [page, pageSize, searchText, filterValues]);

  const fullQueryKey = useMemo(() => [...queryKey, buildParams()], [queryKey, buildParams]);

  const { data, isLoading, isError, error, isFetching } = useQuery({
    queryKey: fullQueryKey,
    queryFn: () => queryFn(buildParams()).then(transformResponse || (d => d)),
    staleTime: queryOptions?.staleTime ?? 1000 * 60,
    gcTime: queryOptions?.gcTime ?? 1000 * 60 * 30,
    retry: queryOptions?.retry ?? 2,
    refetchOnWindowFocus: queryOptions?.refetchOnWindowFocus ?? true,
    refetchInterval: queryOptions?.refetchInterval ?? 1000 * 60 * 60 * 5,
  });

  const loading = isLoading || isFetching;

  const handleTableChange = useCallback((
    pagination: TablePaginationConfig,
    _filters: Record<string, FilterValue | null>,
    _sorter: SorterResult<T> | SorterResult<T>[],
    _extra: TableCurrentDataSource<T>
  ) => {
    if (pagination) {
      if (pagination.current) setPage(pagination.current);
      if (pagination.pageSize) setPageSize(pagination.pageSize);
    }
  }, []);

  const dataSource = data?.items || [];
  const total = data?.total || 0;

  const antdColumns = useMemo(() => columns.map(col => ({
    title: col.title,
    dataIndex: col.dataIndex,
    key: col.key,
    width: col.width,
    align: col.align,
    render: col.render,
    ellipsis: col.ellipsis,
    sorter: col.sorter,
    filterDropdown: col.filterDropdown,
    filters: col.filters,
    onFilter: col.onFilter,
  })), [columns]);

  const paginationConfig = {
    current: page,
    pageSize,
    total,
    showSizeChanger: true,
    showQuickJumper: true,
    pageSizeOptions,
    showTotal: (t: number) => `共 ${t} 条`,
  };

  return (
    <div>
      <TableCard<T>
        dataSource={dataSource}
        columns={antdColumns as any}
        rowKey={rowKey}
        pagination={paginationConfig}
        onTableChange={handleTableChange}
        loading={loading}
        error={isError ? (error as unknown as NormalizedError) : null}
        scroll={{ x: scrollX }}
        size={size}
        bordered={bordered}
        onRow={onRowClick ? (record: T) => ({ onClick: () => onRowClick(record) }) : undefined}
      />
    </div>
  );
}

export interface DataTableHeaderProps<T> {
  title: string;
  search?: DataTableProps<T>['search'];
  filters?: DataTableProps<T>['filters'];
  filterValues: Record<string, unknown>;
  onFilterChange: (key: string, value: unknown) => void;
  onSearch: (value: string) => void;
  searchText: string;
  dataSourceLabel: string;
  dataSourceColor: string;
  dataSourceIcon: React.ReactNode;
  loading: boolean;
  onRefresh: () => void;
  onExport?: () => void;
  extraActions?: React.ReactNode;
  showDataSourceSwitch?: boolean;
  onDataSourceSwitch?: () => void;
  currentDataSource?: 'cache' | 'external' | 'mock';
}

export function DataTableHeader<T>({
  title: _title,
  search,
  filters = [],
  filterValues,
  onFilterChange,
  onSearch,
  searchText,
  dataSourceLabel,
  dataSourceColor,
  dataSourceIcon,
  loading,
  onRefresh,
  onExport,
  extraActions,
  showDataSourceSwitch = false,
  onDataSourceSwitch,
  currentDataSource,
}: DataTableHeaderProps<T>) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          {search && (
            <input
              type="text"
              placeholder={search?.placeholder || '搜索...'}
              value={searchText}
              onChange={(e) => onSearch(e.target.value)}
              style={{ width: 250, padding: '0 12px', height: 32, borderRadius: 6, border: '1px solid var(--color-border-default)', fontSize: 14 }}
            />
          )}
          {filters.map(f => (
            <div key={f.key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {f.type === 'select' && (
                <select
                  value={String(filterValues[f.key] || '')}
                  onChange={(e) => onFilterChange(f.key, e.target.value)}
                  style={{ padding: '0 12px', height: 32, borderRadius: 6, border: '1px solid var(--color-border-default)', fontSize: 14, minWidth: f.style?.width || 140 }}
                >
                  <option value="">全部</option>
                  {f.options?.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                </select>
              )}
              {f.type === 'dateRange' && (
                <input
                  type="text"
                  placeholder={f.placeholder || '日期范围'}
                  value={filterValues[f.key] ? String(filterValues[f.key]) : ''}
                  onChange={(e) => onFilterChange(f.key, e.target.value)}
                  style={{ width: f.style?.width || 300, padding: '0 12px', height: 32, borderRadius: 6, border: '1px solid var(--color-border-default)', fontSize: 14 }}
                />
              )}
              {f.type === 'input' && (
                <input
                  type="text"
                  placeholder={f.placeholder || f.label}
                  value={String(filterValues[f.key] || '')}
                  onChange={(e) => onFilterChange(f.key, e.target.value)}
                  style={{ width: f.style?.width || 200, padding: '0 12px', height: 32, borderRadius: 6, border: '1px solid var(--color-border-default)', fontSize: 14 }}
                />
              )}
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px', borderRadius: 4, background: `${dataSourceColor}10`, color: dataSourceColor, fontSize: 12 }}>
            {dataSourceIcon} {dataSourceLabel}
          </span>
          {showDataSourceSwitch && currentDataSource === 'cache' && (
            <button type="button" onClick={onDataSourceSwitch} style={{ padding: '4px 12px', border: '1px solid var(--color-border-default)', borderRadius: 6, background: 'white', cursor: 'pointer', fontSize: 12 }}>
              切换到实时外部 API
            </button>
          )}
          {showDataSourceSwitch && currentDataSource === 'external' && (
            <button type="button" onClick={onDataSourceSwitch} style={{ padding: '4px 12px', border: '1px solid var(--color-border-default)', borderRadius: 6, background: 'white', cursor: 'pointer', fontSize: 12 }}>
              切换到缓存数据
            </button>
          )}
          {onExport && (
            <button type="button" onClick={onExport} style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '4px 12px', border: '1px solid var(--color-border-default)', borderRadius: 6, background: 'white', cursor: 'pointer' }}>
              <DownloadOutlined /> 导出 CSV
            </button>
          )}
          <button type="button" onClick={onRefresh} disabled={loading} style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '4px 12px', border: '1px solid var(--color-border-default)', borderRadius: 6, background: 'white', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1 }}>
            <ReloadOutlined style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} /> 刷新
          </button>
          {extraActions}
        </div>
      </div>
    </div>
  );
}

export default DataTable;