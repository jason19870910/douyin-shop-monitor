import React, { useState, useMemo, useCallback } from 'react';
import {
  Input,
  Button,
  Space,
  message,
  Tag,
  Avatar,
  Modal,
  Descriptions,
  Tabs,
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  DownloadOutlined,
  UserOutlined,
  VideoCameraOutlined,
  FileOutlined,
} from '@ant-design/icons';
import { creatorApi, type CreatorWork } from '@/api/index';
import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/hooks/useQueries';
import { formatNumber, formatDateTime } from '@/utils/formatters';
import { PageContainer, PageHeader, TableCard } from '@/components/layout';
import { TablePaginationConfig } from 'antd';
import styles from './Creator.module.css';
import type { NormalizedError } from '@/utils/apiClient';

interface Creator {
  creator_id: string;
  nickname?: string;
  creator_name?: string;
  name?: string;
  followers?: number;
  follower_count?: number;
  total_sales: number;
  total_revenue: number;
  product_count: number;
  avg_conversion_rate?: number;
  fetched_at?: string;
  avatar?: string;
  [key: string]: unknown;
}

const Creator = () => {
  const [activeTab, setActiveTab] = useState<'creators' | 'works' | 'videos'>('creators');
  const [searchText, setSearchText] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [detailModal, setDetailModal] = useState<{ visible: boolean; creator: Creator | null }>({
    visible: false,
    creator: null,
  });
  const [workDetailModal, setWorkDetailModal] = useState<{
    visible: boolean;
    work: CreatorWork | null;
  }>({ visible: false, work: null });

  // Creators API - only fetch when 'creators' tab is active
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: queryKeys.creators.list({ page, pageSize, keyword: searchText }),
    queryFn: () => creatorApi.getList({ page, size: pageSize, keyword: searchText }) as Promise<{ items: Creator[]; total: number }>,
    enabled: activeTab === 'creators',
    staleTime: 1000 * 60,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });

  // Works API (内容管理) - only fetch when 'works' tab is active
  const { data: worksData, isLoading: worksLoading, isError: worksIsError, error: worksError, refetch: refetchWorks } = useQuery({
    queryKey: queryKeys.creators.works({ page, pageSize, keyword: searchText, recent_days: 90 }),
    queryFn: () => creatorApi.getWorks({ page, size: pageSize, keyword: searchText, recent_days: 90 }) as Promise<{ items: CreatorWork[]; total: number }>,
    enabled: activeTab === 'works',
    staleTime: 1000 * 60,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });

  // Video Management API (视频管理) - only fetch when 'videos' tab is active
  const { data: videoData, isLoading: videoLoading, isError: videoIsError, error: videoError, refetch: refetchVideos } = useQuery({
    queryKey: queryKeys.creators.externalWorks({ page, pageSize, keyword: searchText, recent_days: 90 }),
    queryFn: () => creatorApi.getExternalWorks({ page, size: pageSize, keyword: searchText, recent_days: 90 }) as Promise<{ items: CreatorWork[]; total: number }>,
    enabled: activeTab === 'videos',
    staleTime: 1000 * 60,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });

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
      setDetailModal({ visible: true, creator: (detail as unknown as Creator) || creator });
    } catch (err) {
      message.error('获取详情失败');
    }
  }, []);

  const handleViewWorkDetail = useCallback((work: CreatorWork) => {
    setWorkDetailModal({ visible: true, work });
  }, []);

  const handleTableChange = (pagination: TablePaginationConfig) => {
    if (pagination && pagination.current !== undefined && pagination.pageSize !== undefined) {
      setPage(pagination.current);
      setPageSize(pagination.pageSize);
    }
  };

  const handleRefetch = () => refetch();
  const handleRefetchWorks = () => refetchWorks();
  const handleRefetchVideos = () => refetchVideos();

  const handleExport = async () => {
    try {
      message.loading('导出中...', 0);
      if (activeTab === 'creators') {
        const result = await creatorApi.getList({ page: 1, size: 10000 });
        message.destroy();

        const csvContent = [
          [
            '创作者ID',
            '昵称',
            '粉丝数',
            '总销量',
            '总收入',
            '带货商品数',
            '平均转化率',
            '更新时间',
          ],
          ...(result?.items || []).map((c) => [
            c.creator_id,
            c.nickname || c.creator_name || c.name || '',
            c.followers ?? c.follower_count ?? 0,
            c.total_sales,
            c.total_revenue,
            c.product_count,
            c.avg_conversion_rate
              ? ((c.avg_conversion_rate as number) * 100).toFixed(2) + '%'
              : '-',
            c.fetched_at,
          ]),
        ]
          .map((row) => row.map((cell) => `"${cell}"`).join(','))
          .join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `creators_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        message.success('导出成功');
      } else if (activeTab === 'works') {
        const result = await creatorApi.getWorks({ page: 1, size: 10000, recent_days: 90 });
        message.destroy();

        const csvContent = [
          [
            '作品ID',
            '标题',
            '创作者',
            '播放量',
            '点赞数',
            '评论数',
            '分享数',
            '状态',
            '创建时间',
            '更新时间',
          ],
          ...(result?.items || []).map((w) => [
            w.work_id,
            w.title || w.name || '',
            w.creator_name || '',
            w.play_count ?? 0,
            w.like_count ?? 0,
            w.comment_count ?? 0,
            w.share_count ?? 0,
            w.status === 1 ? '已发布' : w.status === 2 ? '草稿' : '全部',
            w.create_time || '',
            w.update_time || '',
          ]),
        ]
          .map((row) => row.map((cell) => `"${cell}"`).join(','))
          .join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `creator_works_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        message.success('导出成功');
      } else {
        const result = await creatorApi.getExternalWorks({ page: 1, size: 10000, recent_days: 90 });
        message.destroy();

        const csvContent = [
          [
            '视频ID',
            '标题',
            '创作者',
            '播放量',
            '点赞数',
            '评论数',
            '分享数',
            '状态',
            '创建时间',
            '更新时间',
          ],
          ...(result?.items || []).map((w) => [
            w.work_id,
            w.title || w.name || '',
            w.creator_name || '',
            w.play_count ?? 0,
            w.like_count ?? 0,
            w.comment_count ?? 0,
            w.share_count ?? 0,
            w.status === 1 ? '已发布' : w.status === 2 ? '草稿' : '全部',
            w.create_time || '',
            w.update_time || '',
          ]),
        ]
          .map((row) => row.map((cell) => `"${cell}"`).join(','))
          .join('\n');

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

  const getStatusTag = (status: number | undefined) => {
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

  const creatorColumns = useMemo(
    () => [
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
        render: (avatar: string | undefined) =>
          avatar ? <Avatar src={avatar} size={32} /> : <Avatar size={32} icon={<UserOutlined />} />,
      },
      {
        title: '昵称',
        dataIndex: 'nickname',
        key: 'nickname',
        width: 150,
        render: (_: any, record: Creator) => record.nickname || record.creator_name || record.name || '-',
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
        render: (_: any, record: Creator) => formatNumber(record.followers ?? record.follower_count ?? 0),
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
        render: (v: number | undefined) => (v ? ((v as number) * 100).toFixed(2) + '%' : '-'),
      },
      {
        title: '更新时间',
        dataIndex: 'fetched_at',
        key: 'fetched_at',
        width: 160,
        render: formatDateTime,
      },
    ],
    [handleViewDetail],
  );

  const workColumns = useMemo(
    () => [
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
        render: (coverUrl: string | undefined, record: CreatorWork) =>
          (coverUrl || record.cover) ? (
            <img
              src={coverUrl || record.cover}
              alt="cover"
              style={{ width: 60, height: 60, objectFit: 'cover', borderRadius: 4 }}
            />
          ) : (
            <div
              style={{
                width: 60,
                height: 60,
                background: 'var(--bg-tertiary)',
                borderRadius: 4,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <VideoCameraOutlined />
            </div>
          ),
      },
      {
        title: '标题',
        dataIndex: 'title',
        key: 'title',
        width: 200,
        render: (_: any, record: CreatorWork) => record.title || record.name || '-',
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
        render: (v: any, record: CreatorWork) => v || record.creator_name || '-',
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
    ],
    [handleViewWorkDetail],
  );

  const filteredCreators = useMemo(() => {
    const creators = data?.items || [];
    const searchLower = searchText.toLowerCase();
    return creators.filter(
      (c: Creator) =>
        (c.nickname || c.creator_name || c.name || '').toLowerCase().includes(searchLower) ||
        c.creator_id?.toString().toLowerCase().includes(searchLower),
    );
  }, [data, searchText]);

  const filteredWorks = useMemo(() => {
    const works = worksData?.items || [];
    return works.filter(
      (w: CreatorWork) =>
        w.title?.toLowerCase().includes(searchText.toLowerCase()) ||
        w.creator_name?.toLowerCase().includes(searchText.toLowerCase()) ||
        w.work_id?.toString().toLowerCase().includes(searchText.toLowerCase()),
    );
  }, [worksData, searchText]);

  const filteredVideos = useMemo(() => {
    const videos = videoData?.items || [];
    return videos.filter(
      (v: CreatorWork) =>
        v.title?.toLowerCase().includes(searchText.toLowerCase()) ||
        v.creator_name?.toLowerCase().includes(searchText.toLowerCase()) ||
        v.work_id?.toString().toLowerCase().includes(searchText.toLowerCase()),
    );
  }, [videoData, searchText]);

  return (
    <PageContainer>
      <PageHeader
        title="创作者中心"
        filters={
          <Space className={styles.filters}>
            <Input
              placeholder={
                activeTab === 'creators' ? '搜索创作者昵称/ID...' : '搜索视频标题/创作者/ID...'
              }
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
            <Button icon={<DownloadOutlined />} onClick={handleExport}>
              导出 CSV
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={
                activeTab === 'creators'
                  ? handleRefetch
                  : activeTab === 'works'
                  ? handleRefetchWorks
                  : handleRefetchVideos
              }
              loading={
                activeTab === 'creators'
                  ? isLoading
                  : activeTab === 'works'
                  ? worksLoading
                  : videoLoading
              }
            >
              刷新
            </Button>
          </Space>
        }
      />

      <Tabs activeKey={activeTab} onChange={handleTabChange} className={styles.tabs}>
        <Tabs.TabPane
          tab={
            <span>
              <UserOutlined /> 创作者列表
            </span>
          }
          key="creators"
        />
        <Tabs.TabPane
          tab={
            <span>
              <VideoCameraOutlined /> 内容管理
            </span>
          }
          key="works"
        />
        <Tabs.TabPane
          tab={
            <span>
              <FileOutlined /> 视频管理
            </span>
          }
          key="videos"
        />
      </Tabs>

      {activeTab === 'creators' && (
        <TableCard<Creator>
          dataSource={filteredCreators}
          columns={creatorColumns}
          rowKey="creator_id"
          pagination={{
            current: page,
            pageSize,
            total: data?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total: number) => `共 ${total} 条`,
          }}
          onTableChange={handleTableChange}
          loading={isLoading}
          error={isError ? error as unknown as NormalizedError : null}
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
            total: worksData?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total: number) => `共 ${total} 条`,
          }}
          onTableChange={handleTableChange}
          loading={worksLoading}
          error={worksIsError ? worksError as unknown as NormalizedError : null}
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
            total: videoData?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total: number) => `共 ${total} 条`,
          }}
          onTableChange={handleTableChange}
          loading={videoLoading}
          error={videoIsError ? videoError as unknown as NormalizedError : null}
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
            <Descriptions.Item label="昵称">
              {detailModal.creator.creator_name || detailModal.creator.nickname}
            </Descriptions.Item>
            <Descriptions.Item label="粉丝数">
              {formatNumber(detailModal.creator.follower_count || detailModal.creator.followers)}
            </Descriptions.Item>
            <Descriptions.Item label="总销量">
              {formatNumber(detailModal.creator.total_sales)}
            </Descriptions.Item>
            <Descriptions.Item label="总收入">
              ¥{formatNumber(detailModal.creator.total_revenue)}
            </Descriptions.Item>
            <Descriptions.Item label="带货商品数">
              {formatNumber(detailModal.creator.product_count)}
            </Descriptions.Item>
            <Descriptions.Item label="平均转化率">
              {detailModal.creator.avg_conversion_rate
                ? ((detailModal.creator.avg_conversion_rate as number) * 100).toFixed(2) + '%'
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {formatDateTime(detailModal.creator.fetched_at)}
            </Descriptions.Item>
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
            <Descriptions.Item label="创作者">
              {workDetailModal.work.creator_name}
            </Descriptions.Item>
            <Descriptions.Item label="创作者ID">
              {workDetailModal.work.creator_id}
            </Descriptions.Item>
            <Descriptions.Item label="播放量">
              {formatNumber(workDetailModal.work.play_count)}
            </Descriptions.Item>
            <Descriptions.Item label="点赞数">
              {formatNumber(workDetailModal.work.like_count)}
            </Descriptions.Item>
            <Descriptions.Item label="评论数">
              {formatNumber(workDetailModal.work.comment_count)}
            </Descriptions.Item>
            <Descriptions.Item label="分享数">
              {formatNumber(workDetailModal.work.share_count)}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              {getStatusTag(workDetailModal.work.status)}
            </Descriptions.Item>
            <Descriptions.Item label="时长(秒)">
              {workDetailModal.work.duration || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {formatDateTime(workDetailModal.work.create_time)}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {formatDateTime(workDetailModal.work.update_time)}
            </Descriptions.Item>
            {workDetailModal.work.cover_url && (
              <Descriptions.Item label="封面" span={2}>
                <img
                  src={workDetailModal.work.cover_url}
                  alt="cover"
                  style={{ maxWidth: '100%', height: 'auto', borderRadius: 4 }}
                />
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </PageContainer>
  );
};

export default Creator;