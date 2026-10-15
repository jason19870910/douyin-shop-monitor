import { useMemo } from 'react';
import { formatDate } from '@/utils/formatters';
import { authApi, type AuthStatus } from '@/api/index';
import { DataTable, type DataTableColumn } from '@/components/common';
import { queryKeys } from '@/hooks';

interface AuthStatusWithIndex extends AuthStatus {
  [key: string]: unknown;
}

const Auth = () => {
  const columns = useMemo<DataTableColumn<AuthStatusWithIndex>[]>(() => [
    { title: 'App ID', dataIndex: 'douyin_app_id', key: 'douyin_app_id', width: 200 },
    { title: '重定向 URI', dataIndex: 'redirect_uri', key: 'redirect_uri', width: 300, ellipsis: true },
    { title: '授权状态', dataIndex: 'authorized', key: 'authorized', width: 100 },
    { title: 'Access Token', dataIndex: 'access_token', key: 'access_token', width: 300 },
    { title: '刷新 Token', dataIndex: 'refresh_token', key: 'refresh_token', width: 300 },
    { title: '过期时间', dataIndex: 'expires_at', key: 'expires_at', width: 160, render: (value: unknown) => formatDate(value as string | null | undefined) },
  ], []);

  return (
    <DataTable<AuthStatusWithIndex>
      title="授权状态"
      queryKey={queryKeys.auth.status()}
      queryFn={() => authApi.getStatus().then(res => ({ items: res ? [res] : [], total: res ? 1 : 0 })) as Promise<{ items: AuthStatusWithIndex[]; total: number }>}
      columns={columns}
      rowKey="douyin_app_id"
      search={{ placeholder: '搜索 App ID...' }}
    />
  );
};

export default Auth;