import { useState, useMemo, useCallback, useRef } from 'react';
import type { FormInstance } from 'antd';
import {
  Input,
  Button,
  Select,
  Space,
  Form,
  message,
  Tag,
  Modal,
  Descriptions,
  Switch,
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  DownloadOutlined,
  UserOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import type { TablePaginationConfig, FilterValue, SorterResult, TableCurrentDataSource } from 'antd/es/table/interface';
import { accountApi, type Account } from '@/api/index';
import { useAccountsList, useCreateAccount, useUpdateAccount, useDeleteAccount, queryKeys } from '@/hooks/useQueries';
import { useQueryClient } from '@tanstack/react-query';
import { formatDateTime } from '@/utils/formatters';
import { PageContainer, PageHeader, TableCard } from '@/components/layout';
import styles from '@/styles/common.module.css';
import type { NormalizedError } from '@/utils/apiClient';

type AccountRecord = Account;

interface ColumnItem {
  title: string;
  dataIndex: string;
  key: string;
  width?: number;
  align?: 'left' | 'right' | 'center';
  render?: (value: unknown, record: AccountRecord) => React.ReactNode;
  onCell?: (record: AccountRecord) => { onClick: () => void; style: { cursor: string } };
}

const Account = () => {
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [detailModal, setDetailModal] = useState({
    visible: false,
    account: null as AccountRecord | null,
  });
  const [formModal, setFormModal] = useState({
    visible: false,
    editing: null as AccountRecord | null,
  });
  const formRef = useRef<FormInstance<AccountRecord> | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error, refetch } = useAccountsList({
    page,
    size: pageSize,
    keyword: searchText,
    status: statusFilter,
  });
  const loading = isLoading;
  
  const createAccountMutation = useCreateAccount({
    onSuccess: () => {
      message.success('账号创建成功');
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts.lists() });
    },
    onError: (err) => {
      message.error('创建失败: ' + err.message);
    },
  });

  const updateAccountMutation = useUpdateAccount({
    onSuccess: () => {
      message.success('账号更新成功');
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts.lists() });
    },
    onError: (err) => {
      message.error('更新失败: ' + err.message);
    },
  });

  const deleteAccountMutation = useDeleteAccount({
    onSuccess: () => {
      message.success('账号删除成功');
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts.lists() });
    },
    onError: (err) => {
      message.error('删除失败: ' + err.message);
    },
  });

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value);
    setPage(1);
  };

  const handleStatusChange = (value: string) => {
    setStatusFilter(value);
    setPage(1);
  };

  const handleTableChange = (
    pagination: TablePaginationConfig,
    _filters: Record<string, FilterValue | null>,
    _sorter: SorterResult<AccountRecord> | SorterResult<AccountRecord>[],
    _extra: TableCurrentDataSource<AccountRecord>,
  ) => {
    if (pagination) {
      setPage(pagination.current ?? 1);
      if (pagination.pageSize) setPageSize(pagination.pageSize);
    }
  };

  const handleRefetch = () => refetch();

  const handleViewDetail = useCallback((account: AccountRecord) => {
    setDetailModal({ visible: true, account });
  }, []);

  const handleCreate = useCallback(() => {
    setFormModal({ visible: true, editing: null });
  }, []);

  const handleDelete = useCallback(
    (account: AccountRecord) => {
      if (window.confirm(`确定要删除账号 ${account.account_name} 吗？`)) {
        deleteAccountMutation.mutate(account.account_id);
      }
    },
    [deleteAccountMutation],
  );

  const handleFormSubmit = async (values: Partial<AccountRecord>) => {
    try {
      if (formModal.editing) {
        updateAccountMutation.mutate({ id: formModal.editing.account_id, data: values } as { id: string; data: Partial<AccountRecord> });
      } else {
        createAccountMutation.mutate(values);
      }
      setFormModal({ visible: false, editing: null });
    } catch (err) {
      message.error('保存失败: ' + (err instanceof Error ? err.message : String(err)));
    }
  };

  const handleExport = async () => {
    try {
      message.loading('导出中...', 0);
      const result = await accountApi.getList({ page: 1, size: 10000 });
      message.destroy();

      const csvContent = [
        ['账号ID', '账号名称', '账号类型', '绑定手机', '绑定邮箱', '状态', '最后登录'],
        ...(result?.items || []).map((a: AccountRecord) => [
          a.account_id,
          a.account_name,
          a.account_type,
          a.phone,
          a.email,
          a.status,
          a.last_login,
        ]),
      ]
        .map((row) => row.map((cell: unknown) => `"${String(cell)}"`).join(','))
        .join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `accounts_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      message.success('导出成功');
    } catch (err) {
      message.destroy();
      message.error('导出失败');
    }
  };

  const tableColumns = useMemo<ColumnItem[]>(
    () => [
      {
        title: '账号ID',
        dataIndex: 'account_id',
        key: 'account_id',
        width: 120,
      },
      {
        title: '账号名称',
        dataIndex: 'account_name',
        key: 'account_name',
        width: 150,
        onCell: (record) => ({
          onClick: () => handleViewDetail(record),
          style: { cursor: 'pointer' },
        }),
      },
      {
        title: '账号类型',
        dataIndex: 'account_type',
        key: 'account_type',
        width: 100,
        align: 'center' as const,
        render: (value: unknown) => {
          const type = value as string;
          return (
            <Tag color={type === 'official' ? 'blue' : type === 'personal' ? 'green' : 'orange'}>
              {type === 'official' ? '官方号' : type === 'personal' ? '个人号' : type}
            </Tag>
          );
        },
      },
      {
        title: '绑定手机',
        dataIndex: 'phone',
        key: 'phone',
        width: 150,
      },
      {
        title: '绑定邮箱',
        dataIndex: 'email',
        key: 'email',
        width: 200,
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 100,
        align: 'center' as const,
        render: (value: unknown) => {
          const status = value as string;
          return (
            <Tag color={status === 'active' ? 'green' : status === 'inactive' ? 'orange' : 'red'}>
              {status === 'active' ? '正常' : status === 'inactive' ? '停用' : '异常'}
            </Tag>
          );
        },
      },
      {
        title: '最后登录',
        dataIndex: 'last_login',
        key: 'last_login',
        width: 180,
        render: (value: unknown) => formatDateTime(value as string | null | undefined),
      },
      {
        title: '操作',
        dataIndex: 'action',
        key: 'action',
        width: 180,
        render: (_value: unknown, record: AccountRecord) => (
          <Space>
            <Button type="link" icon={<SettingOutlined />} size="small">
              设置
            </Button>
            <Button type="link" danger size="small" onClick={() => handleDelete(record)}>
              删除
            </Button>
          </Space>
        ),
      },
    ],
    [handleViewDetail, handleDelete],
  );

  const accounts: AccountRecord[] = data?.items || [];
  const total = data?.total || 0;

  return (
    <PageContainer>
      <PageHeader
        title="账号管理"
        filters={
          <Space wrap className={styles.filters}>
            <Input
              placeholder="搜索账号名称/ID..."
              value={searchText}
              onChange={handleSearch}
              prefix={<SearchOutlined />}
              style={{ width: 250 }}
              allowClear
            />
            <Select
              placeholder="账号状态"
              value={statusFilter}
              onChange={handleStatusChange}
              allowClear
              style={{ width: 140 }}
              options={[
                { value: 'active', label: '正常' },
                { value: 'inactive', label: '停用' },
                { value: 'error', label: '异常' },
              ]}
            />
          </Space>
        }
        actions={
          <Space>
            <Button type="primary" icon={<UserOutlined />} onClick={handleCreate}>
              新增账号
            </Button>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>
              导出 CSV
            </Button>
            <Button icon={<ReloadOutlined />} onClick={handleRefetch} loading={loading}>
              刷新
            </Button>
          </Space>
        }
      />

      <TableCard<AccountRecord>
        columns={tableColumns.map((col) => ({
          ...col,
          onCell:
            col.dataIndex === 'account_name'
              ? (record: AccountRecord) => ({
                  onClick: () => handleViewDetail(record),
                  style: { cursor: 'pointer' },
                })
              : undefined,
        }))}
        dataSource={accounts}
        rowKey="account_id"
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total: number) => `共 ${total} 条`,
        }}
        onTableChange={handleTableChange}
        loading={loading}
        error={isError ? error as unknown as NormalizedError : null}
        size="middle"
      />

      <Modal
        title="账号详情"
        visible={detailModal.visible}
        onOk={() => setDetailModal({ ...detailModal, visible: false })}
        onCancel={() => setDetailModal({ ...detailModal, visible: false })}
        width={600}
      >
        {detailModal.account && (
          <Descriptions column={2} title="基本信息">
            <Descriptions.Item label="账号ID">{detailModal.account.account_id}</Descriptions.Item>
            <Descriptions.Item label="账号名称">
              {detailModal.account.account_name}
            </Descriptions.Item>
            <Descriptions.Item label="账号类型">
              {detailModal.account.account_type === 'official'
                ? '官方号'
                : detailModal.account.account_type === 'personal'
                  ? '个人号'
                  : detailModal.account.account_type}
            </Descriptions.Item>
            <Descriptions.Item label="绑定手机">{detailModal.account.phone}</Descriptions.Item>
            <Descriptions.Item label="绑定邮箱">{detailModal.account.email}</Descriptions.Item>
            <Descriptions.Item label="状态">
              {detailModal.account.status === 'active'
                ? '正常'
                : detailModal.account.status === 'inactive'
                  ? '停用'
                  : '异常'}
            </Descriptions.Item>
            <Descriptions.Item label="最后登录">
              {formatDateTime(detailModal.account.last_login)}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      <Modal
        title={formModal.editing ? '编辑账号' : '新增账号'}
        visible={formModal.visible}
        onOk={() =>
          formRef.current
            ?.validateFields()
            .then(handleFormSubmit)
            .catch(() => {})
        }
        onCancel={() => setFormModal({ visible: false, editing: null })}
        width={500}
      >
        <Form ref={formRef} layout="vertical" initialValues={formModal.editing || {}}>
          <Form.Item
            name="account_name"
            label="账号名称"
            rules={[{ required: true, message: '请输入账号名称' }]}
          >
            <Input placeholder="请输入账号名称" />
          </Form.Item>
          <Form.Item
            name="account_type"
            label="账号类型"
            rules={[{ required: true, message: '请选择账号类型' }]}
          >
            <Select placeholder="请选择账号类型">
              <Select.Option value="official">官方号</Select.Option>
              <Select.Option value="personal">个人号</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="phone" label="绑定手机">
            <Input placeholder="请输入手机号" />
          </Form.Item>
          <Form.Item name="email" label="绑定邮箱">
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          <Form.Item name="status" label="状态" valuePropName="checked">
            <Switch checkedChildren="正常" unCheckedChildren="停用" />
          </Form.Item>
        </Form>
      </Modal>
    </PageContainer>
  );
};

export default Account;