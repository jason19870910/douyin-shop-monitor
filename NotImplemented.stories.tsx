import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import NotImplemented from '../pages/NotImplemented';

const meta: Meta<typeof NotImplemented> = {
  title: 'Pages/NotImplemented',
  component: NotImplemented,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    title: { control: 'text' },
    description: { control: 'text' },
    apiEndpoint: { control: 'text' },
  },
};

export default meta;
type Story = StoryObj<typeof NotImplemented>;

export const Default: Story = {
  args: {
    title: '功能开发中',
    description: '该功能正在紧锣密鼓开发中，敬请期待！',
    apiEndpoint: 'GET /api/v1/new-feature',
  },
};

export const VideoEdit: Story = {
  args: {
    title: '视频编辑器',
    description: '提供视频剪辑、特效添加、字幕生成等功能',
    apiEndpoint: 'POST /api/media/video-edit',
  },
};

export const ImageEdit: Story = {
  args: {
    title: '图片编辑器',
    description: '支持图片裁剪、滤镜、水印、文字添加等功能',
    apiEndpoint: 'POST /api/media/image-edit',
  },
};

export const Compliance: Story = {
  args: {
    title: '合规管理',
    description: '商品合规检测、违规申诉、整改跟踪',
    apiEndpoint: 'GET /api/compliance',
  },
};

export const CustomEmpty: Story = {
  args: {
    title: '暂无数据',
    description: '当前条件下没有找到匹配的记录',
    apiEndpoint: '',
  },
};