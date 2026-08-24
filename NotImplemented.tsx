import React from 'react';
import { Card, Alert, Space, Button } from 'antd';
import { ToolOutlined } from '@ant-design/icons';

const NotImplemented = ({ title, description, apiEndpoint }) => (
  <div style={{ padding: 48, textAlign: 'center' }}>
    <Card style={{ maxWidth: 600, margin: '0 auto' }}>
      <div style={{ fontSize: 48, marginBottom: 16 }}>🚧</div>
      <h2 style={{ color: '#1890ff', marginBottom: 16 }}>{title}</h2>
      <p style={{ color: '#595959', marginBottom: 24 }}>{description}</p>
      <Alert
        message="后端 API 未实现"
        description={`需要实现的端点: ${apiEndpoint}`}
        type="warning"
        showIcon
        style={{ marginBottom: 24 }}
      />
      <Space>
        <Button type="primary" icon={<ToolOutlined />}>查看 API 文档</Button>
        <Button>返回仪表盘</Button>
      </Space>
    </Card>
  </div>
);

export default NotImplemented;