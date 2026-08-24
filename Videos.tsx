import React, { useState, useMemo } from 'react';
import dayjs from 'dayjs';
import { Card, Table, Input, Button, Select, Space, Spin, DatePicker, message, Tag } from 'antd';
import { SearchOutlined, ReloadOutlined, DownloadOutlined, EyeOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { videoApi, type Video, type PaginatedResponse } from '@/api/index';
import { useApi } from '@/hooks/useApi';
import { formatNumber, formatStatus, formatDateTime } from '@/utils/formatters';
import { PageContainer, PageHeader, TableCard } from '@/components/layout';
import { NormalizedError } from '@/utils/apiClient';
import styles from './Videos.module.css';

const { RangePicker } = DatePicker;
type DateRangeValue = [dayjs.Dayjs, dayjs.Dayjs] | null;

const Videos = () => {
  const [searchText, setSearchText] = useState('');
  const [dateRange, setDateRange] = useState<DateRangeValue>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const { data, status, error, refetch } = useApi<PaginatedResponse<Video>>(
    () => videoApi.getList({ 
      page, 
      size: pageSize, 
      keyword: searchText,
      start_date: dateRange?.[0]?.format('YYYY-MM-DD'),
      end_date: dateRange?.[1]?.format('YYYY-MM-DD'),
      status: statusFilter,
    }),
    [page, pageSize, searchText, dateRange, statusFilter],
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
    setPage(pagination.current);
    setPageSize(pagination.pageSize);
  };

  const handleExport = async () => {
    try {
      message.loading('导出中...', 0);
      const result = await videoApi.getList({ page: 1, size: 10000 });
      message.destroy();
      
      const csvContent = [
        ['视频ID', '标题', '创作者', '播放量', '点赞数', '评论数', '分享数', '状态', '发布时间'],
        ...(result?.data || []).map(v => [
          v.video_id,
          v.title,
          v.creator_name,
          v.play_count,
          v.like_count,
          v.comment_count,
          v.share_count,
          v.status,
          v.create_time,
        ]),
      ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `videos_${new Date().toISOString().split('T')[0]}.csv`;
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
      width: 150,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 250,
      ellipsis: true,
    },
    {
      title: '创作者',
      dataIndex: 'creator_name',
      key: 'creator_name',
      width: 150,
    },
    {
      title: '播放量',
      dataIndex: 'play_count',
      key: 'play_count',
      align: 'right' as const,
      width: 120,
      render: formatNumber,
    },
    {
      title: '点赞数',
      dataIndex: 'like_count',
      key: 'like_count',
      align: 'right' as const,
      width: 100,
      render: formatNumber,
    },
    {
      title: '评论数',
      dataIndex: 'comment_count',
      key: 'comment_count',
      align: 'right' as const,
      width: 100,
      render: formatNumber,
    },
    {
      title: '分享数',
      dataIndex: 'share_count',
      key: 'share_count',
      align: 'right' as const,
      width: 100,
      render: formatNumber,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      align: 'center' as const,
      render: (status: string) => (
        <Tag color={formatStatus(status).color}>
          {formatStatus(status).text}
        </Tag>
      ),
    },
    {
      title: '发布时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 180,
      render: formatDateTime,
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_, record: Video) => (
        <Space>
          <Button type="link" icon={<EyeOutlined />} size="small">预览</Button>
          <Button type="link" icon={<EditOutlined />} size="small">编辑</Button>
          <Button type="link" icon={<DeleteOutlined />} size="small" danger>删除</Button>
        </Space>
      ),
    },
  ], []);

  const videos = data?.data || [];
  const total = data?.total || 0;

  return (
    <PageContainer>
      <PageHeader
        title="视频管理"
        filters={
          <Space wrap className={styles.filters}>
            <Input
              placeholder="搜索视频标题/创作者..."
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
              placeholder="视频状态"
              value={statusFilter}
              onChange={handleStatusChange}
              allowClear
              style={{ width: 140 }}
              options={[
                { value: 'published', label: '已发布' },
                { value: 'draft', label: '草稿' },
                { value: 'pending', label: '待审核' },
                { value: 'rejected', label: '已驳回' },
              ]}
            />
          </Space>
        }
        actions={
          <Space>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>导出 CSV</Button>
            <Button icon={<ReloadOutlined />} onClick={refetch} loading={loading}>刷新</Button>
          </Space>
        }
      />

      <TableCard<Video>
        dataSource={videos}
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

export default Videos;