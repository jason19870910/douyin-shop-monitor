/**
 * 共享常量定义
 */

// 轮询间隔选项（统一用于 Auth、Profile 等页面）
export const POLLING_INTERVALS = [
  { value: 0, label: '关闭轮询' },
  { value: 10000, label: '10 秒' },
  { value: 30000, label: '30 秒' },
  { value: 60000, label: '1 分钟' },
  { value: 300000, label: '5 分钟' },
];

export type PollingIntervalValue = typeof POLLING_INTERVALS[number]['value'];

// 默认轮询间隔
export const DEFAULT_POLLING_INTERVAL = 30000; // 30 秒