import React, { useState } from 'react';
import { Card, Form, Input, InputNumber, Switch, Button, Space, message, Alert, Divider } from 'antd';
import { ReloadOutlined, CheckOutlined } from '@ant-design/icons';
import { alertApi } from '@/api/index';
import { useApi } from '@/hooks/useApi';
import { PageContainer, PageHeader } from '@/components/layout';
import styles from './AlertConfig.module.css';

const AlertConfig = () => {
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const { data, loading, error, refetch } = useApi(alertApi.getConfig);

  const initialValues = data || {
    sales_drop_threshold: 0.3,
    conversion_drop_threshold: 0.2,
    inventory_low_threshold: 10,
    notification_email: '',
    enabled: true,
  };

  const onFinish = async (values: typeof initialValues) => {
    setSaving(true);
    setSaved(false);
    try {
      await alertApi.updateConfig(values);
      message.success('配置保存成功');
      setSaved(true);
      refetch();
    } catch (err) {
      message.error('保存失败: ' + (err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleEnabledChange = (enabled: boolean) => {
    form.setFieldValue('enabled', enabled);
  };

  if (loading && !data) {
    return (
      <PageContainer>
        <PageHeader title="告警配置" actions={<Button icon={<ReloadOutlined />} onClick={refetch} loading={loading}>刷新</Button>} />
        <Card style={{ padding: 'var(--spacing-10)', textAlign: 'center' }}>
          <div className="ant-spin-dot">
            <span></span><span></span><span></span><span></span>
          </div>
          <p style={{ marginTop: 'var(--spacing-4)', color: 'var(--color-text-tertiary)' }}>加载配置中...</p>
        </Card>
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer>
        <PageHeader title="告警配置" actions={<Button icon={<ReloadOutlined />} onClick={refetch} loading={loading}>刷新</Button>} />
        <Alert message="加载配置失败" description={error.message} type="error" onClick={refetch} action="重试" closable showIcon />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader
        title="告警配置"
        actions={<Button icon={<ReloadOutlined />} onClick={refetch} loading={loading}>刷新</Button>}
      />

      <Card className={styles.alertConfigForm}>
        <Form
          form={form}
          layout="vertical"
          initialValues={initialValues}
          onFinish={onFinish}
          colon={false}
        >
          <Form.Item
            name="enabled"
            label="启用告警"
            valuePropName="checked"
          >
            <Switch onChange={handleEnabledChange} />
          </Form.Item>

          <Divider>销量告警</Divider>

          <Form.Item
            name="sales_drop_threshold"
            label="销量下跌阈值"
            help="当商品销量较前一日下跌超过此比例时触发告警"
            rules={[{ required: true, message: '请输入销量下跌阈值' }]}
          >
            <InputNumber
              min={0.01}
              max={1}
              step={0.01 as const}
              precision={2}
              style={{ width: 150 }}
              formatter={v => v ? `${(v * 100).toFixed(0)}%` : ''}
              parser={(v: string): number | undefined => v ? parseFloat(v.replace('%', '')) / 100 : undefined}
              addonAfter="%"
            />
          </Form.Item>

          <Divider>转化率告警</Divider>

          <Form.Item
            name="conversion_drop_threshold"
            label="转化率下跌阈值"
            help="当商品转化率较前一日下跌超过此比例时触发告警"
            rules={[{ required: true, message: '请输入转化率下跌阈值' }]}
          >
            <InputNumber
              min={0.01}
              max={1}
              step={0.01 as const}
              precision={2}
              style={{ width: 150 }}
              formatter={v => v ? `${(v * 100).toFixed(0)}%` : ''}
              parser={(v: string): number | undefined => v ? parseFloat(v.replace('%', '')) / 100 : undefined}
              addonAfter="%"
            />
          </Form.Item>

          <Divider>库存告警</Divider>

          <Form.Item
            name="inventory_low_threshold"
            label="低库存阈值"
            help="当商品库存低于此数量时触发告警"
            rules={[{ required: true, message: '请输入低库存阈值' }, { type: 'integer', min: 0 }]}
          >
            <InputNumber
              min={0}
              max={10000}
              step={1}
              style={{ width: 150 }}
              addonAfter="件"
            />
          </Form.Item>

          <Divider>通知设置</Divider>

          <Form.Item
            name="notification_email"
            label="告警通知邮箱"
            help="告警触发时将发送邮件通知到此邮箱（留空则不发送邮件）"
            rules={[{ type: 'email', message: '请输入有效的邮箱地址' }]}
          >
            <Input placeholder="admin@example.com" style={{ width: 300 }} />
          </Form.Item>

          <Divider />

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={saving}
                icon={saved ? <CheckOutlined /> : null}
              >
                {saved ? '已保存' : '保存配置'}
              </Button>
              <Button
                onClick={() => {
                  form.setFieldsValue(initialValues);
                  setSaved(false);
                }}
              >
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>

        {saved && (
          <Alert
            message="配置已保存"
            description="告警配置已更新，新的阈值将在下次检查时生效"
            type="success"
            showIcon
            closable
            onClose={() => setSaved(false)}
            style={{ marginTop: 'var(--spacing-4)' }}
          />
        )}
      </Card>

      <Card style={{ marginTop: 'var(--spacing-6)' }}>
        <h3 style={{ marginBottom: 'var(--spacing-4)', fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>告警规则说明</h3>
        <ul style={{ lineHeight: 2, color: 'var(--color-text-secondary)' }}>
          <li><strong>销量下跌告警</strong>：监控每个商品的今日销量与昨日销量对比，当下跌幅度超过设定阈值时触发。</li>
          <li><strong>转化率下跌告警</strong>：监控每个商品的今日转化率与昨日转化率对比，当下跌幅度超过设定阈值时触发。</li>
          <li><strong>低库存告警</strong>：实时监控商品库存，当库存数量低于设定阈值时触发。</li>
          <li><strong>通知方式</strong>：目前支持邮件通知，配置邮箱后将在告警触发时发送邮件。后续可扩展钉钉、企业微信、飞书等通知渠道。</li>
          <li><strong>检查频率</strong>：系统每 5 分钟自动检查一次告警条件，也可在仪表盘点击&ldquo;立即同步&rdquo;手动触发检查。</li>
        </ul>
      </Card>
    </PageContainer>
  );
};

export default AlertConfig;