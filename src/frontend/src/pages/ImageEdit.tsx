import { useMemo } from 'react';
import { formatDate } from '@/utils/formatters';
import { mediaApi, type MediaItem } from '@/api/index';
import { DataTable, type DataTableColumn } from '@/components/common';
import { queryKeys } from '@/hooks';

const ImageEdit = () => {
  const columns = useMemo<DataTableColumn<MediaItem>[]>(() => [
    {
      title: '媒体ID',
      dataIndex: 'media_id',
      key: 'media_id',
      width: 120,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 240,
      ellipsis: true,
    },
    {
      title: '源 URL',
      dataIndex: 'source_url',
      key: 'source_url',
      width: 300,
    },
    {
      title: '输出 URL',
      dataIndex: 'output_url',
      key: 'output_url',
      width: 300,
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
    <DataTable<MediaItem>
      title="图片素材"
      queryKey={queryKeys.media.imageEdit({})}
      queryFn={(params) => mediaApi.getImageEditList(params) as Promise<{ items: MediaItem[]; total: number }>}
      columns={columns}
      rowKey="media_id"
      search={{ placeholder: '搜索媒体...' }}
    />
  );
};

export default ImageEdit;