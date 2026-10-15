import { useMemo } from 'react';
import { formatNumber, formatDate } from '@/utils/formatters';
import { videoApi, type Video } from '@/api/index';
import { DataTable, type DataTableColumn } from '@/components/common';
import { queryKeys } from '@/hooks';

const Videos = () => {
  const columns = useMemo<DataTableColumn<Video>[]>(() => [
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
      width: 240,
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
      align: 'right',
      width: 100,
      render: (value: unknown) => formatNumber(value as number | null | undefined),
    },
    {
      title: '点赞数',
      dataIndex: 'like_count',
      key: 'like_count',
      align: 'right',
      width: 100,
      render: (value: unknown) => formatNumber(value as number | null | undefined),
    },
    {
      title: '评论数',
      dataIndex: 'comment_count',
      key: 'comment_count',
      align: 'right',
      width: 100,
      render: (value: unknown) => formatNumber(value as number | null | undefined),
    },
    {
      title: '分享数',
      dataIndex: 'share_count',
      key: 'share_count',
      align: 'right',
      width: 100,
      render: (value: unknown) => formatNumber(value as number | null | undefined),
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 160,
      render: (value: unknown) => formatDate(value as string | null | undefined),
    },
  ], []);

  return (
    <DataTable<Video>
      title="视频管理"
      queryKey={queryKeys.videos.list({})}
      queryFn={(params) => videoApi.getList(params) as Promise<{ items: Video[]; total: number }>}
      columns={columns}
      rowKey="video_id"
      search={{ placeholder: '搜索视频标题/创作者...' }}
      exportConfig={{
        filenamePrefix: 'videos',
        columns: [
          { key: 'video_id', label: '视频ID' },
          { key: 'title', label: '标题' },
          { key: 'creator_name', label: '创作者' },
          { key: 'play_count', label: '播放量' },
          { key: 'like_count', label: '点赞数' },
          { key: 'comment_count', label: '评论数' },
          { key: 'share_count', label: '分享数' },
          { key: 'create_time', label: '创建时间' },
        ],
      }}
    />
  );
};

export default Videos;