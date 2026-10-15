import { useState } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Switch,
  Button,
  Space,
  message,
  Alert,
  Divider,
  Tabs,
  Select,
} from 'antd';
import { ReloadOutlined, CheckOutlined, ShopOutlined, BellOutlined } from '@ant-design/icons';
import { alertDianApi, type AlertConfig } from '@/api/index';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageContainer, PageHeader } from '@/components/layout';
import styles from '@/styles/alertCommon.module.css';

const AlertsDian = () => {
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['alerts', 'dian', 'config'],
    queryFn: () => alertDianApi.getConfig() as Promise<AlertConfig | undefined>,
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });

  const updateConfigMutation = useMutation({
    mutationFn: (alertConfig: AlertConfig) => alertDianApi.updateConfig(alertConfig) as Promise<AlertConfig | undefined>,
    onSuccess: () => {
      message.success('抖店告警配置保存成功');
      setSaved(true);
      queryClient.invalidateQueries({ queryKey: ['alerts', 'dian', 'config'] });
    },
    onError: (err) => {
      message.error('保存失败: ' + (err as Error).message)
    },
    onSettled: () => {
      setSaving(false);
    },
  });

  const defaultValues: AlertConfig = {
    product_sales_drop_threshold: 0.3,
    order_refund_rate_threshold: 0.15,
    compliance_risk_threshold: 'medium',
    notification_email: '',
    enabled: true,
  };

  const initialValues = data || defaultValues;

  const onFinish = async (values: AlertConfig) => {
    setSaving(true);
    setSaved(false);
    updateConfigMutation.mutate(values);
  };

  const handleEnabledChange = (enabled: boolean) => {
    form.setFieldValue('enabled', enabled);
  };

  const handleRefetch = () => refetch();

  if (isLoading && !data) {
    return (
      <PageContainer>
        <PageHeader
          title={
            <>
              <ShopOutlined style={{ marginRight: 'var(--spacing-2)' }} />
              <BellOutlined
                style={{ marginLeft: 'var(--spacing-2)', marginRight: 'var(--spacing-2)' }}
              />{' '}
              抖店告警配置
            </>
          }
          actions={
            <Button icon={<ReloadOutlined />} onClick={handleRefetch} loading={isLoading}>
              刷新
            </Button>
          }
        />
        <Card style={{ padding: 'var(--spacing-10)', textAlign: 'center' }}>
          <div className="ant-spin-dot">
            <span></span>
            <span></span>
            <span></span>
            <span></span>
          </div>
          <p style={{ marginTop: 'var(--spacing-4)', color: 'var(--color-text-tertiary)' }}>
            加载配置中...
          </p>
        </Card>
      </PageContainer>
    );
  }

  if (isError) {
    return (
      <PageContainer>
        <PageHeader
          title={
            <>
              <ShopOutlined style={{ marginRight: 'var(--spacing-2)' }} />
              <BellOutlined
                style={{ marginLeft: 'var(--spacing-2)', marginRight: 'var(--spacing-2)' }}
              />{' '}
              抖店告警配置
            </>
          }
          actions={
            <Button icon={<ReloadOutlined />} onClick={handleRefetch} loading={isLoading}>
              刷新
            </Button>
          }
        />
        <Alert
          message="加载配置失败"
          description={error.message}
          type="error"
          onClick={handleRefetch}
          action="重试"
          closable
          showIcon
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader
        title={
          <>
            <ShopOutlined style={{ marginRight: 'var(--spacing-2)' }} />
            <BellOutlined
              style={{ marginLeft: 'var(--spacing-2)', marginRight: 'var(--spacing-2)' }}
            />{' '}
            抖店告警配置
          </>
        }
        actions={
          <Button icon={<ReloadOutlined />} onClick={handleRefetch} loading={isLoading}>
            刷新
          </Button>
        }
      />

      <Tabs defaultActiveKey="sales">
        <Tabs.TabPane tab="销量告警" key="sales">
          <Card className={styles.alertConfigForm}>
            <Form
              form={form}
              layout="vertical"
              initialValues={initialValues}
              onFinish={onFinish}
              colon={false}
            >
              <Form.Item name="enabled" label="启用抖店告警" valuePropName="checked">
                <Switch onChange={handleEnabledChange} />
              </Form.Item>

              <Divider>商品销量告警</Divider>

              <Form.Item
                name="product_sales_drop_threshold"
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
                  formatter={(value: number | undefined) => (value !== undefined && value !== null ? `${(value * 100).toFixed(0)}%` : '')}
                  parser={(displayValue: string | undefined): number =>
                    displayValue ? parseFloat(displayValue.replace('%', '')) / 100 : 0
                  }
                  addonAfter="%"
                />
              </Form.Item>

              <Divider>订单退款率告警</Divider>

              <Form.Item
                name="order_refund_rate_threshold"
                label="退款率上升阈值"
                help="当订单退款率较前一日上升超过此比例时触发告警"
                rules={[{ required: true, message: '请输入退款率上升阈值' }]}
              >
                <InputNumber
                  min={0.01}
                  max={1}
                  step={0.01 as const}
                  precision={2}
                  style={{ width: 150 }}
                  formatter={(value: number | undefined) => (value !== undefined && value !== null ? `${(value * 100).toFixed(0)}%` : '')}
                  parser={(displayValue: string | undefined): number =>
                    displayValue ? parseFloat(displayValue.replace('%', '')) / 100 : 0
                  }
                  addonAfter="%"
                />
              </Form.Item>

              <Divider>合规风险告警</Divider>

              <Form.Item
                name="compliance_risk_threshold"
                label="合规风险等级阈值"
                help="当商品合规风险等级达到或超过此级别时触发告警"
                rules={[{ required: true, message: '请选择合规风险等级' }]}
              >
                <Select style={{ width: 150 }}>
                  <Select.Option value="low">低风险</Select.Option>
                  <Select.Option value="medium">中风险</Select.Option>
                  <Select.Option value="high">高风险</Select.Option>
                </Select>
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
                description="抖店告警配置已更新，新的阈值将在下次检查时生效"
                type="success"
                showIcon
                closable
                onClose={() => setSaved(false)}
                style={{ marginTop: 'var(--spacing-4)' }}
              />
            )}
          </Card>
        </Tabs.TabPane>

        <Tabs.TabPane tab="告警规则" key="rules">
          <Card style={{ marginTop: 'var(--spacing-6)' }}>
            <h3
              style={{
                marginBottom: 'var(--spacing-4)',
                fontSize: 'var(--font-size-lg)',
                fontWeight: 'var(--font-weight-semibold)',
                color: 'var(--color-text-primary)',
              }}
            >
              抖店告警规则说明
            </h3>
            <ul style={{ lineHeight: 2, color: 'var(--color-text-secondary)' }}>
              <li>
                <strong>商品销量下跌告警</strong>
                ：监控每个商品的今日销量与昨日销量对比，当下跌幅度超过设定阈值时触发。
              </li>
              <li>
                <strong>订单退款率上升告警</strong>
                ：监控每日订单退款率，当退款率上升超过设定阈值时触发。
              </li>
              <li>
                <strong>合规风险等级告警</strong>
                ：监控商品合规风险等级，当风险等级达到或超过设定阈值时触发。
              </li>
              <li>
                <strong>通知方式</strong>
                ：目前支持邮件通知，配置邮箱后将在告警触发时发送邮件。后续可扩展钉钉、企业微信、飞书等通知渠道。
              </li>
              <li>
                <strong>检查频率</strong>：系统每 5
                分钟自动检查一次告警条件，也可在仪表盘点击&ldquo;立即同步&rdquo;手动触发检查。
              </li>
              <li>
                <strong>平台范围</strong>：本配置仅针对抖店平台（商品、订单、店铺）的数据。
              </li>
            </ul>
          </Card>
        </Tabs.TabPane>
      </Tabs>
    </PageContainer>
  );
};

export default AlertsDian;