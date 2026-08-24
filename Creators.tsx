import React, { useState, useMemo, useCallback } from 'react';
import { Card, Table, Input, Button, Space, Spin, Tag, Avatar, message, Descriptions, Modal } from 'antd';
import { SearchOutlined, ReloadOutlined, DownloadOutlined, UserOutlined } from '@ant-design/icons';
import { creatorApi, type Creator, type PaginatedResponse } from '@/api/index';
import { useApi } from '@/hooks/useApi';
import { formatNumber, formatDateTime } from '@/utils/formatters';

const Creators = () => {
  const [searchText, setSearchText] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [detailModal, setDetailModal] = useState<{ visible: boolean; creator: Creator | null }>({ visible: false, creator: null });

  const { data, status, error, refetch } = useApi<PaginatedResponse<Creator>>(
    () => creatorApi.getList(),
    [],
    { retryOnError: true }
  );
  const loading = status === 'loading';

  const handleSearch = (e) => {
    setSearchText(e.target.value);
  };

  const handleViewDetail = useCallback(async (creator: Creator) => {
    try {
      const detail = await creatorApi.getDetail(creator.creator_id);
      setDetailModal({ visible: true, creator: detail || creator });
    } catch (err) {
      message.error('获取详情失败');
    }
  }, []);

  const handleTableChange = (pagination) => {
    if (pagination) {
      setPage(pagination.current);
      setPageSize(pagination.pageSize);
    }
  };

  const handleExport = async () => {
    try {
      message.loading('导出中...', 0);
      const result = await creatorApi.getList();
      message.destroy();
      
      const csvContent = [
        ['创作者ID', '昵称', '粉丝数', '总销量', '总收入', '带货商品数', '更新时间'],
        ...(result?.data || []).map(c => [
          c.creator_id,
          c.nickname,
          c.followers,
          c.total_sales,
          c.total_revenue,
          c.product_count,
          c.fetched_at,
        ]),
      ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `creators_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      message.success('导出成功');
    } catch (err) {
      message.destroy();
      message.error('导出失败');
    }
  };

  const columns = useMemo(() => [
    {
      title: '创作者ID',
      dataIndex: 'creator_id',
      key: 'creator_id',
      width: 120,
    },
    {
      title: '头像',
      dataIndex: 'avatar',
      key: 'avatar',
      width: 60,
      render: (avatar) => avatar ? <Avatar src={avatar} size={32} /> : <Avatar size={32} icon={<UserOutlined />} />,
    },
    {
      title: '昵称',
      dataIndex: 'nickname',
      key: 'nickname',
      width: 150,
      onCell: (record: Creator) => ({
        onClick: () => handleViewDetail(record),
        style: { cursor: 'pointer' },
      }),
    },
    {
      title: '粉丝数',
      dataIndex: 'followers',
      key: 'followers',
      align: 'right' as const,
      width: 100,
      render: formatNumber,
    },
    {
      title: '总销量',
      dataIndex: 'total_sales',
      key: 'total_sales',
      align: 'right' as const,
      width: 100,
      render: formatNumber,
    },
    {
      title: '总收入',
      dataIndex: 'total_revenue',
      key: 'total_revenue',
      align: 'right' as const,
      width: 120,
      render: (v) => '¥' + formatNumber(v),
    },
    {
      title: '带货商品数',
      dataIndex: 'product_count',
      key: 'product_count',
      align: 'right' as const,
      width: 100,
      render: formatNumber,
    },
    {
      title: '更新时间',
      dataIndex: 'fetched_at',
      key: 'fetched_at',
      width: 160,
      render: formatDateTime,
    },
  ], [handleViewDetail]);

  const filteredData = useMemo(() => {
    const creators = (data?.data as Creator[]) || [];
    return creators.filter((c: Creator) => 
      c.nickname?.toLowerCase().includes(searchText.toLowerCase()) ||
      c.creator_id?.toString().toLowerCase().includes(searchText.toLowerCase())
    );
  }, [data, searchText]
  );

  if (loading && !data) {
    return <Spin size="large" tip="加载创作者数据..." />;
  }

  if (error) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <p style={{ color: '#ff4d4f' }}>加载失败: {error.message}</p>
          <Button type="primary" onClick={refetch} icon={<ReloadOutlined />}>
            重试
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">创作者管理</h1>
        <Space>
          <Input
            placeholder="搜索创作者昵称/ID..."
            value={searchText}
            onChange={handleSearch}
            prefix={<SearchOutlined />}
            style={{ width: 250 }}
            allowClear
          />
          <Button icon={<DownloadOutlined />} onClick={handleExport}>导出 CSV</Button>
          <Button icon={<ReloadOutlined />} onClick={refetch} loading={loading}>刷新</Button>
        </Space>
      </div>

      <Card className="table-container">
        <Table
          columns={columns}
          dataSource={filteredData}
          pagination={{
            current: page,
            pageSize,
            total: filteredData.length,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          onChange={handleTableChange}
          rowKey="creator_id"
          loading={loading}
        />
      </Card>

      <Modal
        title="创作者详情"
        visible={detailModal.visible}
        onOk={() => setDetailModal({ ...detailModal, visible: false })}
        onCancel={() => setDetailModal({ ...detailModal, visible: false })}
        width={600}
      >
        {detailModal.creator && (
          <Descriptions column={2} title="基本信息">
            <Descriptions.Item label="创作者ID">{detailModal.creator.creator_id}</Descriptions.Item>
            <Descriptions.Item label="昵称">{detailModal.creator.creator_name || detailModal.creator.nickname}</Descriptions.Item>
            <Descriptions.Item label="粉丝数">{formatNumber(detailModal.creator.follower_count || detailModal.creator.followers)}</Descriptions.Item>
            <Descriptions.Item label="总销量">{formatNumber(detailModal.creator.total_sales)}</Descriptions.Item>
            <Descriptions.Item label="总收入">¥{formatNumber(detailModal.creator.total_revenue)}</Descriptions.Item>
            <Descriptions.Item label="带货商品数">{formatNumber(detailModal.creator.product_count)}</Descriptions.Item>
            <Descriptions.Item label="平均转化率">{detailModal.creator.avg_conversion_rate ? ((detailModal.creator.avg_conversion_rate as number) * 100).toFixed(2) + '%' : '-'}</Descriptions.Item>
            <Descriptions.Item label="更新时间">{formatDateTime(detailModal.creator.fetched_at)}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default Creators;