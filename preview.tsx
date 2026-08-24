import type { Preview } from '@storybook/react';
import React from 'react';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import '../src/index.css';

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#f0f2f5' },
        { name: 'dark', value: '#141414' },
        { name: 'white', value: '#ffffff' },
      ],
    },
    layout: 'centered',
  },
  decorators: [
    (Story) => (
      <ConfigProvider locale={zhCN} theme={{ token: { colorPrimary: '#1890ff' } }}>
        <div style={{ minWidth: 320, padding: 16 }}>
          <Story />
        </div>
      </ConfigProvider>
    ),
  ],
  globalTypes: {
    locale: {
      description: 'Internationalization locale',
      defaultValue: 'zh-CN',
      toolbar: {
        title: 'Locale',
        icon: 'globe',
        items: ['zh-CN', 'en-US'],
        dynamicTitle: true,
      },
    },
  },
};

export default preview;