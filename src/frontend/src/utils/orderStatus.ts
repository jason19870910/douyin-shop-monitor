/**
 * Order status normalization utility.
 * Maps FXG (抖店) API raw status values to standardized internal statuses.
 */

import { colors } from '@/theme/tokens';

// FXG order status mapping from raw API values to internal standardized statuses
const FXG_STATUS_MAP: Record<string, string> = {
  // 待付款/未支付
  'unpaid': 'pending',
  'wait_buyer_pay': 'pending',

  // 待发货/处理中
  'handling': 'pending',
  'await_ship': 'pending',
  'await_ship_and_logistics': 'pending',
  'exp_ship': 'pending',
  'exp_ship_and_logistics': 'pending',
  'ship_delay': 'pending',
  'ship_and_logistics_delay': 'pending',
  'sku_order_wait_settle': 'pending',

  // 已发货/发货中
  'on_delivery': 'shipped',
  'shipped': 'shipped',
  'delivered': 'shipped',

  // 已完成/已签收
  'completed': 'completed',
  'signed': 'completed',
  'delivery_aftersale': 'completed',
  'stock_aftersale': 'completed',

  // 已取消
  'cancelled': 'cancelled',
  'buyer_cancelled': 'cancelled',
  'seller_cancelled': 'cancelled',

  // 退款/售后
  'refunded': 'refunded',
  'refunding': 'refunded',
  'return_refund': 'refunded',
  'stock_up': 'refunded',

  // 异常
  'ship_exception': 'cancelled',
  'warning': 'pending',
};

/**
 * Normalize a raw FXG order status to a standardized internal status.
 * @param rawStatus - Raw status from FXG API
 * @returns Normalized status (completed, pending, shipped, cancelled, refunded, unknown)
 */
export function normalizeOrderStatus(rawStatus: unknown): string {
  if (!rawStatus || typeof rawStatus !== 'string') {
    return 'unknown';
  }

  const normalized = rawStatus.toLowerCase().trim();

  // Direct mapping
  if (FXG_STATUS_MAP[normalized]) {
    return FXG_STATUS_MAP[normalized];
  }

  // Fuzzy matching for partial matches
  if (normalized.includes('cancel') || normalized.includes('取消')) {
    return 'cancelled';
  }
  if (normalized.includes('refund') || normalized.includes('退款') || normalized.includes('退货')) {
    return 'refunded';
  }
  if (normalized.includes('ship') || normalized.includes('发货') || normalized.includes('派送') || normalized.includes('送达')) {
    return 'shipped';
  }
  if (normalized.includes('complete') || normalized.includes('完成') || normalized.includes('签收') || normalized.includes('结束')) {
    return 'completed';
  }
  if (normalized.includes('pay') || normalized.includes('付款') || normalized.includes('待') || normalized.includes('处理')) {
    return 'pending';
  }

  return 'unknown';
}

/**
 * Get display label for a normalized status.
 */
export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    completed: '已完成',
    pending: '待处理',
    shipped: '已发货',
    cancelled: '已取消',
    refunded: '已退款',
    unknown: '未知',
  };
  return labels[status] || status;
}

/**
 * Get color for a normalized status (for Ant Design Tag).
 */
export function getStatusColor(status: string): string {
  const antdColors: Record<string, string> = {
    completed: 'green',
    pending: 'orange',
    shipped: 'blue',
    cancelled: 'red',
    refunded: 'purple',
    unknown: 'default',
  };
  return antdColors[status] || 'default';
}

/**
 * Get hex color for a normalized status (for Recharts).
 * Uses design tokens from tokens.ts to avoid hardcoded values.
 */
export function getStatusHexColor(status: string): string {
  const colorMap: Record<string, string> = {
    completed: colors.success[500],      // #52c41a
    pending: colors.warning[500],        // #faad14
    shipped: colors.info[500],           // #3b82f6 (replaces #1890ff)
    cancelled: colors.error[500],        // #ff4d4f
    refunded: '#722ed1',                 // Purple - not in tokens, keep for now
    unknown: colors.neutral[400],        // #bfbfbf (replaces #d9d9d9)
  };
  return colorMap[status] || colors.neutral[400];
}

/**
 * Normalize an array of orders by adding normalized_status field.
 */
export function normalizeOrders<T extends { status?: string }>(orders: T[]): (T & { normalized_status: string })[] {
  return orders.map((order) => ({
    ...order,
    normalized_status: normalizeOrderStatus(order.status),
  }));
}