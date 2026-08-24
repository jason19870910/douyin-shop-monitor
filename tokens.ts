export const colors = {
  primary: {
    50: '#e6f4ff',
    100: '#bae0ff',
    200: '#91caff',
    300: '#69b1ff',
    400: '#4096ff',
    500: '#1890ff',
    600: '#096dd9',
    700: '#0050b3',
    800: '#003a8c',
    900: '#002766',
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
  neutral: {
    0: '#ffffff',
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#f0f0f0',
    300: '#d9d9d9',
    400: '#bfbfbf',
    500: '#8c8c8c',
    600: '#595959',
    700: '#434343',
    800: '#262626',
    900: '#1f1f1f',
    950: '#141414',
    1000: '#000000',
  },
  bg: {
    primary: '#f0f2f5',
    secondary: '#ffffff',
    tertiary: '#fafafa',
    inverted: '#001529',
  },
  text: {
    primary: '#1f1f1f',
    secondary: '#595959',
    tertiary: '#8c8c8c',
    quaternary: '#bfbfbf',
    inverted: '#ffffff',
    link: '#1890ff',
    danger: '#ff4d4f',
  },
  border: {
    light: '#f0f0f0',
    default: '#d9d9d9',
    dark: '#bfbfbf',
  },
  trend: {
    up: '#ff4d4f',
    down: '#52c41a',
    flat: '#595959',
  },
  status: {
    published: '#52c41a',
    draft: '#1890ff',
    pending: '#faad14',
    rejected: '#ff4d4f',
    completed: '#52c41a',
    cancelled: '#ff4d4f',
    refunded: '#1890ff',
    editing: '#722ed1',
    failed: '#ff4d4f',
    active: '#52c41a',
    inactive: '#faad14',
    high: '#ff4d4f',
    medium: '#faad14',
    low: '#52c41a',
    ignored: '#1890ff',
    resolved: '#52c41a',
  },
  sider: {
    bg: '#001529',
    border: 'rgba(255, 255, 255, 0.1)',
    textPrimary: '#ffffff',
    textSecondary: 'rgba(255, 255, 255, 0.65)',
    textMuted: 'rgba(255, 255, 255, 0.45)',
    hover: 'rgba(255, 255, 255, 0.08)',
    selected: '#1890ff',
    selectedHover: 'rgba(24, 144, 255, 0.1)',
    collapseBtnBorder: 'rgba(255, 255, 255, 0.1)',
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