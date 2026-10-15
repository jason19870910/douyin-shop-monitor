import type { Meta, StoryObj } from '@storybook/react';
import { formatNumber, formatCurrency, formatPercent, formatDateTime, formatDate, formatStatus, calculateGrowth, getTrendClass } from '../utils/formatters';

const meta: Meta<any> = {
  title: 'Utilities/Formatters',
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {},
};

export default meta;

type Story = StoryObj<any>;

export const FormatNumber: Story = {
  render: () => {
    const testCases = [
      { input: 0, expected: '0' },
      { input: 100, expected: '100' },
      { input: 1000, expected: '1,000' },
      { input: 10000, expected: '1.00万' },
      { input: 100000, expected: '10.00万' },
      { input: 1000000, expected: '100.00万' },
      { input: 100000000, expected: '1.00亿' },
      { input: 123456789, expected: '1.23亿' },
      { input: null, expected: '0' },
      { input: undefined, expected: '0' },
    ];

    return (
      <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'monospace' }}>
        <thead>
          <tr style={{ background: '#f5f5f5' }}>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Input</th>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Output</th>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Expected</th>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Match</th>
          </tr>
        </thead>
        <tbody>
          {testCases.map(({ input, expected }, index) => {
            const output = formatNumber(input);
            const match = output === expected;
            return (
              <tr key={index} style={{ background: index % 2 === 0 ? '#fff' : '#fafafa' }}>
                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{String(input)}</td>
                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{output}</td>
                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{expected}</td>
                <td style={{ padding: '8px', border: '1px solid #ddd', color: match ? '#52c41a' : '#ff4d4f' }}>
                  {match ? '✅' : '❌'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    ),
  },
};

export const FormatCurrency: Story = {
  render: () => {
    const testCases = [0, 100, 1000, 10000, 123456.78, null, undefined];

    return (
      <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'monospace' }}>
        <thead>
          <tr style={{ background: '#f5f5f5' }}>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Input</th>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Output</th>
          </tr>
        </thead>
        <tbody>
          {testCases.map((input, index) => (
            <tr key={index} style={{ background: index % 2 === 0 ? '#fff' : '#fafafa' }}>
              <td style={{ padding: '8px', border: '1px solid #ddd' }}>{String(input)}</td>
              <td style={{ padding: '8px', border: '1px solid #ddd' }}>{formatCurrency(input)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    ),
  },
};

export const FormatPercent: Story = {
  render: () => {
    const testCases = [0, 0.01, 0.032, 0.12, 0.5, 1, 1.5, null, undefined];

    return (
      <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'monospace' }}>
        <thead>
          <tr style={{ background: '#f5f5f5' }}>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Input</th>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Output</th>
          </tr>
        </thead>
        <tbody>
          {testCases.map((input, index) => (
            <tr key={index} style={{ background: index % 2 === 0 ? '#fff' : '#fafafa' }}>
              <td style={{ padding: '8px', border: '1px solid #ddd' }}>{String(input)}</td>
              <td style={{ padding: '8px', border: '1px solid #ddd' }}>{formatPercent(input)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    ),
  },
};

export const FormatDateTime: Story = {
  render: () => {
    const testCases = [
      '2026-08-18T10:30:45.123Z',
      '2026-08-18T10:30:45',
      '2026-01-01',
      null,
      undefined,
      '',
    ];

    return (
      <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'monospace' }}>
        <thead>
          <tr style={{ background: '#f5f5f5' }}>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Input</th>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>formatDateTime</th>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>formatDate</th>
          </tr>
        </thead>
        <tbody>
          {testCases.map((input, index) => (
            <tr key={index} style={{ background: index % 2 === 0 ? '#fff' : '#fafafa' }}>
              <td style={{ padding: '8px', border: '1px solid #ddd' }}>{String(input)}</td>
              <td style={{ padding: '8px', border: '1px solid #ddd' }}>{formatDateTime(input)}</td>
              <td style={{ padding: '8px', border: '1px solid #ddd' }}>{formatDate(input)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    ),
  },
};

export const FormatStatus: Story = {
  render: () => {
    const statuses = [
      'published', 'draft', 'pending', 'rejected',
      'completed', 'cancelled', 'refunded', 'editing', 'failed',
      'active', 'inactive', 'error',
      'high', 'medium', 'low',
      'ignored', 'resolved',
      'unknown_status',
    ];

    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {statuses.map((status) => {
          const config = formatStatus(status);
          return (
            <span
              key={status}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '4px 12px',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: 500,
                background: config.color === 'success' ? '#f6ffed' :
                           config.color === 'warning' ? '#fffbe6' :
                           config.color === 'error' ? '#fff1f0' :
                           config.color === 'processing' ? '#e6f7ff' :
                           '#f5f5f5',
                color: config.color === 'success' ? '#52c41a' :
                       config.color === 'warning' ? '#faad14' :
                       config.color === 'error' ? '#ff4d4f' :
                       config.color === 'processing' ? '#1890ff' :
                       '#595959',
                border: `1px solid ${config.color === 'success' ? '#b7eb8f' :
                                                config.color === 'warning' ? '#ffe58f' :
                                                config.color === 'error' ? '#ffccc7' :
                                                config.color === 'processing' ? '#91d5ff' :
                                                '#d9d9d9'}`,
              }}
            >
              {status} → {config.text}
            </span>
          );
        })}
      </div>
    ),
  },
};

export const CalculateGrowth: Story = {
  render: () => {
    const testCases = [
      { current: 120, previous: 100, desc: '增长 20%' },
      { current: 80, previous: 100, desc: '下降 20%' },
      { current: 100, previous: 100, desc: '持平' },
      { current: 100, previous: 0, desc: '从 0 增长' },
      { current: 0, previous: 100, desc: '归零' },
      { current: 0, previous: 0, desc: '均为 0' },
    ];

    return (
      <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'monospace' }}>
        <thead>
          <tr style={{ background: '#f5f5f5' }}>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Current</th>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Previous</th>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Growth %</th>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Trend Class</th>
            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Description</th>
          </tr>
        </thead>
        <tbody>
          {testCases.map(({ current, previous, desc }, index) => {
            const growth = calculateGrowth(current, previous);
            const trend = getTrendClass(current, previous);
            return (
              <tr key={index} style={{ background: index % 2 === 0 ? '#fff' : '#fafafa' }}>
                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{current}</td>
                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{previous}</td>
                <td style={{ padding: '8px', border: '1px solid #ddd', color: growth > 0 ? '#ff4d4f' : growth < 0 ? '#52c41a' : '#595959' }}>
                  {growth > 0 ? '↑' : growth < 0 ? '↓' : '→'} {Math.abs(growth).toFixed(1)}%
                </td>
                <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    background: trend === 'up' ? '#fff1f0' : trend === 'down' ? '#f6ffed' : '#f5f5f5',
                    color: trend === 'up' ? '#ff4d4f' : trend === 'down' ? '#52c41a' : '#8c8c8c',
                  }}>
                    {trend || '无'}
                  </span>
                </td>
                <td style={{ padding: '8px', border: '1px solid #ddd', color: '#888' }}>{desc}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    ),
  },
};