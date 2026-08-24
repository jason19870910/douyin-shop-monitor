import React, { useState, useMemo } from 'react';
import dayjs from 'dayjs';
import { Card, Table, Input, Button, Select, Space, Spin, DatePicker, message, Tag } from 'antd';
import { SearchOutlined, ReloadOutlined, DownloadOutlined, VideoCameraAddOutlined, PlayCircleOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { mediaApi, type MediaItem, type PaginatedResponse } from '@/api/index';
import { useApi } from '@/hooks/useApi';
import { formatNumber, formatDateTime } from '@/utils/formatters';
import { PageContainer, PageHeader, TableCard } from '@/components/layout';
import { NormalizedError } from '@/utils/apiClient';
import styles from './VideoEdit.module.css';

const { RangePicker } = DatePicker;
type DateRangeValue = [dayjs.Dayjs, dayjs.Dayjs] | null;

const VideoEdit = () => {
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [dateRange, setDateRange] = useState<DateRangeValue>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const { data, status, error, refetch } = useApi<PaginatedResponse<MediaItem>>(
    () => mediaApi.getVideoEditList({ 
      page, 
      size: pageSize, 
      keyword: searchText,
      status: statusFilter,
      start_date: dateRange?.[0]?.format('YYYY-MM-DD'),
      end_date: dateRange?.[1]?.format('YYYY-MM-DD'),
    }),
    [page, pageSize, searchText, statusFilter, dateRange],
    { retryOnError: true }
  );
  const loading = status === 'loading';

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value);
    setPage(1);
  };

  const handleDateChange = (dates: DateRangeValue) => {
    setDateRange(dates);
    setPage(1);
  };

  const handleStatusChange = (value: string) => {
    setStatusFilter(value);
    setPage(1);
  };

  const handleTableChange = (pagination: { current: number; pageSize: number }) => {
    if (pagination) {
      setPage(pagination.current);
      setPageSize(pagination.pageSize);
    }
  };

  const handleStartEdit = async (record: MediaItem) => {
    try {
      message.loading('启动编辑...', 0);
      message.destroy();
      message.success('编辑任务已启动');
      refetch();
    } catch (err) {
      message.destroy();
      message.error('启动失败');
    }
  };

  const handleNewEdit = () => {
    message.info('新建编辑任务功能开发中...');
  };

  const handleExport = async () => {
    try {
      message.loading('导出中...', 0);
      const result = await mediaApi.getVideoEditList({ page: 1, size: 10000 });
      message.destroy();
      
      const csvContent = [
        ['视频ID', '标题', '原始素材', '编辑状态', '输出格式', '时长(秒)', '文件大小', '创建时间'],
        ...(result?.data || []).map(v => [
          v.video_id,
          v.title,
          v.source_material,
          v.edit_status,
          v.output_format,
          v.duration,
          v.file_size,
          v.create_time,
        ]),
      ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `video_edit_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      message.success('导出成功');
    } catch (err) {
      message.destroy();
      message.error('导出失败');
    }
  };

  const columns = useMemo(() => [
    {
      title: '视频ID',
      dataIndex: 'video_id',
      key: 'video_id',
      width: 120,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 200,
      ellipsis: true,
    },
    {
      title: '原始素材',
      dataIndex: 'source_material',
      key: 'source_material',
      width: 150,
    },
    {
      title: '编辑状态',
      dataIndex: 'edit_status',
      key: 'edit_status',
      width: 100,
      align: 'center' as const,
      render: (status: string) => (
        <Tag color={status === 'editing' ? 'processing' : status === 'completed' ? 'success' : 'default'}>
          {status === 'editing' ? '编辑中' : status === 'completed' ? '已完成' : status}
        </Tag>
      ),
    },
    {
      title: '输出格式',
      dataIndex: 'output_format',
      key: 'output_format',
      width: 100,
    },
    {
      title: '时长(秒)',
      dataIndex: 'duration',
      key: 'duration',
      align: 'right' as const,
      width: 100,
      render: formatNumber,
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 120,
      render: (v: number | undefined) => v ? (v / 1024 / 1024).toFixed(2) + ' MB' : '-',
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 180,
      render: formatDateTime,
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_, record: MediaItem) => (
        <Space>
          <Button type="link" icon={<PlayCircleOutlined />} size="small">预览</Button>
          <Button type="link" icon={<EditOutlined />} size="small">编辑</Button>
          <Button type="link" icon={<DeleteOutlined />} size="small" danger>删除</Button>
        </Space>
      ),
    },
  ], []);

  const videoList = data?.data || [];
  const total = data?.total || 0;

  return (
    <PageContainer>
      <PageHeader
        title="视频编辑"
        filters={
          <Space wrap className={styles.filters}>
            <Input
              placeholder="搜索视频标题..."
              value={searchText}
              onChange={handleSearch}
              prefix={<SearchOutlined />}
              style={{ width: 250 }}
              allowClear
            />
            <RangePicker
              value={dateRange}
              onChange={handleDateChange}
              placeholder={['开始日期', '结束日期']}
              style={{ width: 300 }}
              allowClear
            />
            <Select
              placeholder="编辑状态"
              value={statusFilter}
              onChange={handleStatusChange}
              allowClear
              style={{ width: 140 }}
              options={[
                { value: 'editing', label: '编辑中' },
                { value: 'completed', label: '已完成' },
                { value: 'failed', label: '失败' },
              ]}
            />
          </Space>
        }
        actions={
          <Space>
            <Button type="primary" icon={<VideoCameraAddOutlined />} onClick={handleNewEdit}>新建编辑任务</Button>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>导出 CSV</Button>
            <Button icon={<ReloadOutlined />} onClick={refetch} loading={loading}>刷新</Button>
          </Space>
        }
      />

      <TableCard<MediaItem>
        dataSource={videoList}
        columns={columns}
        rowKey="video_id"
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
        error={error}
        scroll={{ x: 1300 }}
        size="middle"
      />
    </PageContainer>
  );
};

export default VideoEdit;