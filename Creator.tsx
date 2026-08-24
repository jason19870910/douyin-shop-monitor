import React, { useState, useMemo, useCallback } from 'react';
import { Card, Table, Input, Button, Space, Spin, message, Tag, Avatar, Modal, Descriptions, Tabs } from 'antd';
import { SearchOutlined, ReloadOutlined, DownloadOutlined, UserOutlined, VideoCameraOutlined, FileOutlined } from '@ant-design/icons';
import { creatorApi, type Creator, type CreatorWork, type PaginatedResponse } from '@/api/index';
import { useApi } from '@/hooks/useApi';
import { formatNumber, formatDateTime } from '@/utils/formatters';
import { PageContainer, PageHeader, TableCard } from '@/components/layout';
import { NormalizedError } from '@/utils/apiClient';
import styles from './Creator.module.css';

const Creator = () => {
  const [activeTab, setActiveTab] = useState<'creators' | 'works' | 'videos'>('creators');
  const [searchText, setSearchText] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [detailModal, setDetailModal] = useState<{ visible: boolean; creator: Creator | null }>({ visible: false, creator: null });
  const [workDetailModal, setWorkDetailModal] = useState<{ visible: boolean; work: CreatorWork | null }>({ visible: false, work: null });

  // Creators API
  const { data, status, error, refetch } = useApi<PaginatedResponse<Creator>>(
    () => creatorApi.getList({ page, size: pageSize, keyword: searchText }),
    [page, pageSize, searchText],
    { retryOnError: true }
  );

  // Works API (内容管理)
  const { data: worksData, status: worksStatus, error: worksError, refetch: refetchWorks } = useApi<PaginatedResponse<CreatorWork>>(
    () => creatorApi.getWorks({ page, size: pageSize, keyword: searchText }),
    [page, pageSize, searchText],
    { retryOnError: true }
  );

  // Video Management API (视频管理 - 可使用外部 API 实时获取)
  const { data: videoData, status: videoStatus, error: videoError, refetch: refetchVideos } = useApi<PaginatedResponse<CreatorWork>>(
    () => creatorApi.getExternalWorks({ page, size: pageSize, keyword: searchText }),
    [page, pageSize, searchText],
    { retryOnError: true }
  );

  const loading = status === 'loading';
  const worksLoading = worksStatus === 'loading';
  const videoLoading = videoStatus === 'loading';

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value);
    setPage(1);
  };

  const handleTabChange = (key: string) => {
    setActiveTab(key as 'creators' | 'works' | 'videos');
    setSearchText('');
    setPage(1);
  };

  const handleViewDetail = useCallback(async (creator: Creator) => {
    try {
      const detail = await creatorApi.getDetail(creator.creator_id);
      setDetailModal({ visible: true, creator: detail || creator });
    } catch (err) {
      message.error('获取详情失败');
    }
  }, []);

  const handleViewWorkDetail = useCallback((work: CreatorWork) => {
    setWorkDetailModal({ visible: true, work });
  }, []);

  const handleTableChange = (pagination: { current: number; pageSize: number }) => {
    if (pagination) {
      setPage(pagination.current);
      setPageSize(pagination.pageSize);
    }
  };

  const handleExport = async () => {
    try {
      message.loading('导出中...', 0);
      if (activeTab === 'creators') {
        const result = await creatorApi.getList({ page: 1, size: 10000 });
        message.destroy();
        
        const csvContent = [
          ['创作者ID', '昵称', '粉丝数', '总销量', '总收入', '带货商品数', '平均转化率', '更新时间'],
          ...(result?.data || []).map(c => [
            c.creator_id,
            c.nickname,
            c.followers,
            c.total_sales,
            c.total_revenue,
            c.product_count,
            c.avg_conversion_rate ? ((c.avg_conversion_rate as number) * 100).toFixed(2) + '%' : '-',
            c.fetched_at,
          ]),
        ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `creators_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        message.success('导出成功');
      } else if (activeTab === 'works') {
        const result = await creatorApi.getWorks({ page: 1, size: 10000 });
        message.destroy();
        
        const csvContent = [
          ['作品ID', '标题', '创作者', '播放量', '点赞数', '评论数', '分享数', '状态', '创建时间', '更新时间'],
          ...(result?.data || []).map(w => [
            w.work_id,
            w.title,
            w.creator_name,
            w.play_count,
            w.like_count,
            w.comment_count,
            w.share_count,
            w.status === 1 ? '已发布' : w.status === 2 ? '草稿' : '全部',
            w.create_time,
            w.update_time,
          ]),
        ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `creator_works_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        message.success('导出成功');
      } else {
        const result = await creatorApi.getExternalWorks({ page: 1, size: 10000 });
        message.destroy();
        
        const csvContent = [
          ['视频ID', '标题', '创作者', '播放量', '点赞数', '评论数', '分享数', '状态', '创建时间', '更新时间'],
          ...(result?.data || []).map(w => [
            w.work_id,
            w.title,
            w.creator_name,
            w.play_count,
            w.like_count,
            w.comment_count,
            w.share_count,
            w.status === 1 ? '已发布' : w.status === 2 ? '草稿' : '全部',
            w.create_time,
            w.update_time,
          ]),
        ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `creator_videos_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        message.success('导出成功');
      }
    } catch (err) {
      message.destroy();
      message.error('导出失败');
    }
  };

  const getStatusTag = (status: number) => {
    switch (status) {
      case 1:
        return <Tag color="green">已发布</Tag>;
      case 2:
        return <Tag color="orange">草稿</Tag>;
      case 3:
        return <Tag color="red">审核中</Tag>;
      case 4:
        return <Tag color="volcano">已驳回</Tag>;
      default:
        return <Tag color="default">全部</Tag>;
    }
  };

  const creatorColumns = useMemo(() => [
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
      render: (avatar: string | undefined) => avatar ? <Avatar src={avatar} size={32} /> : <Avatar size={32} icon={<UserOutlined />} />,
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
      render: (v: number) => '¥' + formatNumber(v),
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
      title: '平均转化率',
      dataIndex: 'avg_conversion_rate',
      key: 'avg_conversion_rate',
      align: 'right' as const,
      width: 120,
      render: (v: number | undefined) => v ? ((v as number) * 100).toFixed(2) + '%' : '-',
    },
    {
      title: '更新时间',
      dataIndex: 'fetched_at',
      key: 'fetched_at',
      width: 160,
      render: formatDateTime,
    },
  ], [handleViewDetail]);

  const workColumns = useMemo(() => [
    {
      title: '作品ID',
      dataIndex: 'work_id',
      key: 'work_id',
      width: 120,
    },
    {
      title: '封面',
      dataIndex: 'cover_url',
      key: 'cover_url',
      width: 80,
      render: (coverUrl: string | undefined) => coverUrl ? (
        <img src={coverUrl} alt="cover" style={{ width: 60, height: 60, objectFit: 'cover', borderRadius: 4 }} />
      ) : (
        <div style={{ width: 60, height: 60, background: '#f0f0f0', borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <VideoCameraOutlined />
        </div>
      ),
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 200,
      onCell: (record: CreatorWork) => ({
        onClick: () => handleViewWorkDetail(record),
        style: { cursor: 'pointer' },
      }),
    },
    {
      title: '创作者',
      dataIndex: 'creator_name',
      key: 'creator_name',
      width: 120,
    },
    {
      title: '播放量',
      dataIndex: 'play_count',
      key: 'play_count',
      align: 'right' as const,
      width: 100,
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
      render: getStatusTag,
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 160,
      render: formatDateTime,
    },
    {
      title: '更新时间',
      dataIndex: 'update_time',
      key: 'update_time',
      width: 160,
      render: formatDateTime,
    },
  ], [handleViewWorkDetail]);

  const filteredCreators = useMemo(() => {
    const creators = (data?.data as Creator[]) || [];
    return creators.filter((c: Creator) => 
      c.nickname?.toLowerCase().includes(searchText.toLowerCase()) ||
      c.creator_id?.toString().toLowerCase().includes(searchText.toLowerCase())
    );
  }, [data, searchText]);

  const filteredWorks = useMemo(() => {
    const works = (worksData?.data as CreatorWork[]) || [];
    return works.filter((w: CreatorWork) => 
      w.title?.toLowerCase().includes(searchText.toLowerCase()) ||
      w.creator_name?.toLowerCase().includes(searchText.toLowerCase()) ||
      w.work_id?.toString().toLowerCase().includes(searchText.toLowerCase())
    );
  }, [worksData, searchText]);

  const filteredVideos = useMemo(() => {
    const videos = (videoData?.data as CreatorWork[]) || [];
    return videos.filter((v: CreatorWork) => 
      v.title?.toLowerCase().includes(searchText.toLowerCase()) ||
      v.creator_name?.toLowerCase().includes(searchText.toLowerCase()) ||
      v.work_id?.toString().toLowerCase().includes(searchText.toLowerCase())
    );
  }, [videoData, searchText]);

  return (
    <PageContainer>
      <PageHeader
        title="创作者中心"
        filters={
          <Space className={styles.filters}>
            <Input
              placeholder={activeTab === 'creators' ? '搜索创作者昵称/ID...' : '搜索视频标题/创作者/ID...'}
              value={searchText}
              onChange={handleSearch}
              prefix={<SearchOutlined />}
              style={{ width: 250 }}
              allowClear
            />
          </Space>
        }
        actions={
          <Space>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>导出 CSV</Button>
            <Button icon={<ReloadOutlined />} onClick={
              activeTab === 'creators' ? refetch :
              activeTab === 'works' ? refetchWorks : refetchVideos
            } loading={
              activeTab === 'creators' ? loading :
              activeTab === 'works' ? worksLoading : videoLoading
            }>刷新</Button>
          </Space>
        }
      />

      <Tabs activeKey={activeTab} onChange={handleTabChange} className={styles.tabs}>
        <Tabs.TabPane tab={<span><UserOutlined /> 创作者列表</span>} key="creators" />
        <Tabs.TabPane tab={<span><VideoCameraOutlined /> 内容管理</span>} key="works" />
        <Tabs.TabPane tab={<span><FileOutlined /> 视频管理</span>} key="videos" />
      </Tabs>

      {activeTab === 'creators' && (
        <TableCard<Creator>
          dataSource={filteredCreators}
          columns={creatorColumns}
          rowKey="creator_id"
          pagination={{
            current: page,
            pageSize,
            total: filteredCreators.length,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total: number) => `共 ${total} 条`,
          }}
          onTableChange={handleTableChange}
          loading={loading}
          error={error}
        />
      )}

      {activeTab === 'works' && (
        <TableCard<CreatorWork>
          dataSource={filteredWorks}
          columns={workColumns}
          rowKey="work_id"
          pagination={{
            current: page,
            pageSize,
            total: filteredWorks.length,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total: number) => `共 ${total} 条`,
          }}
          onTableChange={handleTableChange}
          loading={worksLoading}
          error={worksError}
        />
      )}

      {activeTab === 'videos' && (
        <TableCard<CreatorWork>
          dataSource={filteredVideos}
          columns={workColumns}
          rowKey="work_id"
          pagination={{
            current: page,
            pageSize,
            total: filteredVideos.length,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total: number) => `共 ${total} 条`,
          }}
          onTableChange={handleTableChange}
          loading={videoLoading}
          error={videoError}
        />
      )}

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

      <Modal
        title="作品详情"
        visible={workDetailModal.visible}
        onOk={() => setWorkDetailModal({ ...workDetailModal, visible: false })}
        onCancel={() => setWorkDetailModal({ ...workDetailModal, visible: false })}
        width={700}
      >
        {workDetailModal.work && (
          <Descriptions column={2} title="作品信息">
            <Descriptions.Item label="作品ID">{workDetailModal.work.work_id}</Descriptions.Item>
            <Descriptions.Item label="标题">{workDetailModal.work.title}</Descriptions.Item>
            <Descriptions.Item label="创作者">{workDetailModal.work.creator_name}</Descriptions.Item>
            <Descriptions.Item label="创作者ID">{workDetailModal.work.creator_id}</Descriptions.Item>
            <Descriptions.Item label="播放量">{formatNumber(workDetailModal.work.play_count)}</Descriptions.Item>
            <Descriptions.Item label="点赞数">{formatNumber(workDetailModal.work.like_count)}</Descriptions.Item>
            <Descriptions.Item label="评论数">{formatNumber(workDetailModal.work.comment_count)}</Descriptions.Item>
            <Descriptions.Item label="分享数">{formatNumber(workDetailModal.work.share_count)}</Descriptions.Item>
            <Descriptions.Item label="状态">{getStatusTag(workDetailModal.work.status)}</Descriptions.Item>
            <Descriptions.Item label="时长(秒)">{workDetailModal.work.duration || '-'}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{formatDateTime(workDetailModal.work.create_time)}</Descriptions.Item>
            <Descriptions.Item label="更新时间">{formatDateTime(workDetailModal.work.update_time)}</Descriptions.Item>
            {workDetailModal.work.cover_url && (
              <Descriptions.Item label="封面" span={2}>
                <img src={workDetailModal.work.cover_url} alt="cover" style={{ maxWidth: '100%', height: 'auto', borderRadius: 4 }} />
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </PageContainer>
  );
};

export default Creator;