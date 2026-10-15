import { useMemo } from 'react';
import { formatDate, formatNumber } from '@/utils/formatters';
import { mediaApi, type MediaItem as Video } from '@/api/index';
import { DataTable, type DataTableColumn } from '@/components/common';
import { queryKeys } from '@/hooks';

const VideoEdit = () => {
  const columns = useMemo<DataTableColumn<Video>[]>(() => [
    {
      title: '视频ID',
      dataIndex: 'media_id',
      key: 'media_id',
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
      title: '封面',
      dataIndex: 'cover',
      key: 'cover',
      width: 80,
      render: (value: unknown) =>
        (value as string | undefined) ? <img src={value as string} alt="cover" style={{ width: 40, height: 40, borderRadius: 4 }} /> : null,
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
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 160,
      render: (value: unknown) => formatDate(value as string | null | undefined),
    },
  ], []);

  return (
    <DataTable<Video>
      title="视频素材"
      queryKey={queryKeys.media.videoEdit({})}
      queryFn={(params) => mediaApi.getVideoEditList(params) as Promise<{ items: Video[]; total: number }>}
      columns={columns}
      rowKey="media_id"
      search={{ placeholder: '搜索视频...' }}
    />
  );
};

export default VideoEdit;