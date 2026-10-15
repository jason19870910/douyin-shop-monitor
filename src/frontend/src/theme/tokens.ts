export const colors = {
  primary: {
    50: '#e6f4ff',
    100: '#bae0ff',
    200: '#91caff',
    300: '#69b1ff',
    400: '#4096ff',
    500: '#66A3FF',
    600: '#4A90E2',
    700: '#357ABD',
    800: '#2A5F9A',
    900: '#1F3A6B',
  },
  success: {
    50: '#f6ffed',
    100: '#d9f7be',
    200: '#b7eb8f',
    300: '#95de64',
    400: '#73d13d',
    500: '#52c41a',
    600: '#389e0d',
    700: '#237804',
    800: '#135200',
    900: '#092b00',
  },
  warning: {
    50: '#fffbe6',
    100: '#fff1b8',
    200: '#ffe58f',
    300: '#ffd666',
    400: '#ffc53d',
    500: '#faad14',
    600: '#d48806',
    700: '#ad6800',
    800: '#874d00',
    900: '#613400',
  },
  error: {
    50: '#fff1f0',
    100: '#ffccc7',
    200: '#ffa39e',
    300: '#ff7875',
    400: '#ff4d4f',
    500: '#ff4d4f',
    600: '#d9363e',
    700: '#bf262a',
    800: '#921d21',
    900: '#681316',
  },
  info: {
    50: '#eff6ff',
    100: '#dbe4ff',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
  },
  neutral: {
    0: '#FFFFFF',          /* 浅色主题：纯白 */
    50: '#FAFAFA',         /* 浅色主题：极白 */
    100: '#F5F5F5',        /* 浅色主题：次白 */
    200: '#E5E5E5',        /* 浅色主题：浅灰 */
    300: '#D4D4D4',        /* 浅色主题：轻灰 */
    400: '#bfbfbf',        /* 保留兼容 */
    500: '#8c8c8c',        /* 浅色主题：中灰 */
    600: '#595959',        /* 浅色主题：深灰 */
    700: '#434343',        /* 浅色主题：更深灰 */
    800: '#262626',        /* 浅色主题：较深灰 */
    900: '#1f1f1f',        /* 浅色主题：深灰 */
    950: '#141414',        /* 保留兼容 */
    1000: '#000000',       /* 保留兼容 */
  },
  bg: {
    primary: '#FFFFFF',      /* 浅色主题：页面背景 */
    secondary: '#FAFAFA',    /* 浅色主题：卡片底色 */
    tertiary: '#F5F5F5',     /* 浅色主题：卡片表头 */
    hover: '#F0F2F5',        /* 浅色主题：行hover */
  },
  text: {
    primary: '#18181B',      /* 浅色主题：深黑主文本 */
    secondary: '#86868B',    /* 浅色主题：中灰次文本 */
    muted: '#7C757F',        /* 浅色主题：辅助文本 */
  },
  border: {
    color: '#D1D9E1',        /* 浅色主题：柔和边框 */
    glow: 'rgba(0, 212, 255, 0.15)', /* 浅色主题：微光边框 */
  },
  shadow: {
    card: '0 2px 10px rgba(0, 0, 0, 0.05)', /* 浅色主题：轻微阴影 */
    glowOnline: '0 0 8px rgba(34, 197, 94, 0.30)', /* 在线指示灯光晕 */
    glowBlue: '0 0 6px rgba(0, 212, 255, 0.20)', /* 卡片hover发光 */
  },
  accent: {
    blue: '#66A3FF',         /* 浅色主题：淡化强调蓝 */
  },
  brand: {
    purple: '#A0A4FF',       /* 浅色主题：淡化品牌紫 */
  },
  trend: {
    up: '#ff4d4f',
    down: '#52c41a',
    flat: '#595959',
  },
  status: {
    published: '#28A745',    /* 成功绿 */
    draft: '#3b82f6',        /* 草稿蓝 */
    pending: '#FFB400',      /* 待发货橙 */
    rejected: '#DC3545',     /* 错误红 */
    completed: '#28A745',    /* 已完成绿 */
    cancelled: '#DC3545',    /* 取消红 */
    refunded: '#3b82f6',     /* 退款蓝 */
    editing: '#722ed1',      /* 编辑紫 */
    failed: '#DC3545',       /* 失败红 */
    active: '#28A745',       /* 激活绿 */
    inactive: '#FAF3F7',     /* 非激活淡紫 */
    high: '#DC3545',         /* 高优先级红 */
    medium: '#FFB400',       /* 中优先级橙 */
    low: '#28A745',          /* 低优先级绿 */
    ignored: '#6B7280',      /* 已忽略中灰 */
  },
  sider: {
    bg: '#FFFFFF',           /* 浅色主题：侧边栏背景 */
    border: 'rgba(0, 0, 0, 0.05)', /* 浅色主题：侧边栏边框 */
    textPrimary: '#18181B',  /* 浅色主题：主文本 */
    textSecondary: '#86868B',/* 浅色主题：次文本 */
    textMuted: '#7C757F',    /* 浅色主题： muted文本 */
    hover: 'rgba(0, 0, 0, 0.03)', /* 浅色主题：悬停 */
    selected: '#3B82F6',     /* 浅色主题：选中蓝 */
    selectedHover: 'rgba(59, 130, 246, 0.1)', /* 浅色主题：选中悬停 */
    collapseBtnBorder: 'rgba(0, 0, 0, 0.1)', /* 折叠按钮边框 */
  },
} as const;

export const spacing = {
  0: 0,
  1: 4,
  2: 8,
  3: 12,
  4: 16,
  5: 20,
  6: 24,
  7: 28,
  8: 32,
  9: 36,
  10: 40,
  12: 48,
  16: 64,
} as const;

export const borderRadius = {
  none: 0,
  sm: 4,
  md: 6,
  lg: 8,
  xl: 12,
  '2xl': 16,
  full: 9999,
} as const;

export const shadows = {
  none: 'none',
  sm: '0 1px 2px rgba(0, 0, 0, 0.03)',
  md: '0 1px 4px rgba(0, 0, 0, 0.08)',
  lg: '0 4px 12px rgba(0, 0, 0, 0.1)',
  xl: '0 8px 24px rgba(0, 0, 0, 0.12)',
  sider: '2px 0 8px rgba(0, 0, 0, 0.08)',
  cardHover: '0 4px 12px rgba(0, 0, 0, 0.1)',
} as const;

export const typography = {
  fontFamily: {
    base: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
    mono: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
  },
  fontSize: {
    xs: 12,
    sm: 13,
    base: 14,
    lg: 16,
    xl: 18,
    '2xl': 20,
    '3xl': 24,
    '4xl': 28,
    '5xl': 32,
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: 1.4,
    normal: 1.57,
    relaxed: 1.7,
  },
} as const;

export const zIndex = {
  base: 0,
  dropdown: 100,
  sticky: 200,
  fixed: 300,
  modal: 1000,
  popover: 1100,
  tooltip: 1200,
  sider: 100,
  header: 90,
} as const;

export const breakpoints = {
  xs: 480,
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200,
  xxl: 1600,
} as const;

export const transitions = {
  fast: '0.15s ease',
  base: '0.2s ease',
  slow: '0.3s ease',
} as const;

export const layout = {
  siderWidth: 200,
  siderCollapsedWidth: 80,
  headerHeight: 64,
  contentPadding: spacing[6],
} as const;

export type Colors = typeof colors;
export type Spacing = typeof spacing;
export type BorderRadius = typeof borderRadius;
export type Shadows = typeof shadows;
export type Typography = typeof typography;
export type ZIndex = typeof zIndex;
export type Breakpoints = typeof breakpoints;
export type Transitions = typeof transitions;
export type Layout = typeof layout;