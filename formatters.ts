export type StatusColor = 'default' | 'success' | 'warning' | 'error' | 'processing' | 'green' | 'blue' | 'orange' | 'red';

export interface StatusConfig {
  color: StatusColor;
  text: string;
}

export function formatNumber(num: number | null | undefined): string {
  if (num === null || num === undefined) return '0';
  if (num >= 100000000) {
    return (num / 100000000).toFixed(2) + '亿';
  }
  if (num >= 10000) {
    return (num / 10000).toFixed(2) + '万';
  }
  return num.toLocaleString();
}

export function formatCurrency(num: number | null | undefined): string {
  if (num === null || num === undefined) return '¥0';
  return '¥' + formatNumber(num);
}

export function formatPercent(num: number | null | undefined): string {
  if (num === null || num === undefined) return '0%';
  return (num * 100).toFixed(2) + '%';
}

export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

export function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatStatus(status: string): StatusConfig {
  const statusMap: Record<string, StatusConfig> = {
    published: { color: 'green', text: '已发布' },
    draft: { color: 'blue', text: '草稿' },
    pending: { color: 'orange', text: '待审核' },
    rejected: { color: 'red', text: '已驳回' },
    completed: { color: 'success', text: '已完成' },
    cancelled: { color: 'red', text: '已取消' },
    refunded: { color: 'blue', text: '已退款' },
    editing: { color: 'processing', text: '编辑中' },
    failed: { color: 'error', text: '失败' },
    active: { color: 'green', text: '正常' },
    inactive: { color: 'orange', text: '停用' },
    error: { color: 'red', text: '异常' },
    high: { color: 'error', text: '高风险' },
    medium: { color: 'warning', text: '中风险' },
    low: { color: 'success', text: '低风险' },
    ignored: { color: 'blue', text: '已忽略' },
    resolved: { color: 'green', text: '已解决' },
  };
  return statusMap[status] || { color: 'default', text: status };
}

export function getTrendClass(current: number, previous: number): string {
  if (previous === 0) return '';
  return current > previous ? 'up' : current < previous ? 'down' : '';
}

export function calculateGrowth(current: number, previous: number | null | undefined): number {
  if (!previous || previous === 0) return current > 0 ? 100 : 0;
  return ((current - previous) / previous) * 100;
}