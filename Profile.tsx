import React, { useState } from 'react';
import { Card, Descriptions, Button, Space, Avatar, message, Form, Input, Typography, Divider, Alert } from 'antd';
import { UserOutlined, EditOutlined, LockOutlined, SaveOutlined, LoadingOutlined, ReloadOutlined } from '@ant-design/icons';
import { useApi } from '@/hooks/useApi';
import { authApi, type AuthStatus } from '@/api/index';
import { PageContainer, PageHeader } from '@/components/layout';
import styles from './Profile.module.css';

const { Title } = Typography;

const Profile = () => {
  const [isEditing, setIsEditing] = useState(false);
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);

  const { data: authData, status: authStatus, error: authError, refetch: refetchAuth } = useApi<AuthStatus>(
    authApi.getStatus,
    [],
    { retryOnError: true }
  );
  const authLoading = authStatus === 'loading';

  const userInfo = authData;

  const handleEdit = () => {
    if (userInfo) {
      form.setFieldsValue({
        accountName: userInfo.douyin_app_id,
        email: userInfo.redirect_uri,
        phone: '',
      });
      setIsEditing(true);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    form.resetFields();
  };

  interface ProfileFormValues {
  accountName: string;
  email: string;
  phone: string;
  refreshToken?: string;
}

const handleSave = async (values: ProfileFormValues) => {
    setSaving(true);
    try {
      message.success('个人信息更新功能待后端 API 支持');
      setIsEditing(false);
    } catch (err) {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  if (authLoading) {
    return (
      <PageContainer>
        <PageHeader title="个人中心" />
        <Card style={{ maxWidth: 700, margin: 'var(--spacing-12) auto' }}>
          <div style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
            <LoadingOutlined style={{ fontSize: 24, color: 'var(--color-primary-500)' }} spin />
            <p style={{ marginTop: 'var(--spacing-4)', color: 'var(--color-text-tertiary)' }}>加载用户信息中...</p>
          </div>
        </Card>
      </PageContainer>
    );
  }

  if (authError || !userInfo) {
    return (
      <PageContainer>
        <PageHeader title="个人中心" />
        <Card style={{ maxWidth: 700, margin: 'var(--spacing-12) auto' }}>
          <Alert
            message="无法获取用户信息"
            description={authError?.message || '用户未授权或会话已过期'}
            type="error"
            showIcon
            style={{ margin: 'var(--spacing-6)' }}
          />
          <Space style={{ margin: '0 var(--spacing-6) var(--spacing-6)' }}>
            <Button type="primary" onClick={refetchAuth} icon={<ReloadOutlined />}>
              重试
            </Button>
            <Button onClick={() => { if (typeof window !== 'undefined') window.location.href = '/auth'; }}>
              去授权
            </Button>
          </Space>
        </Card>
      </PageContainer>
    );
  }

  const profileData = {
    accountName: userInfo.douyin_app_id,
    accountType: '抖音开放平台应用',
    authorizationStatus: userInfo.authorized ? '已授权' : '未授权',
    accessTokenExpires: userInfo.expires_at
      ? new Date(userInfo.expires_at).toLocaleString('zh-CN')
      : '永不过期',
    scope: userInfo.scope?.join(', ') || '无',
    redirectUri: userInfo.redirect_uri,
  };

  return (
    <PageContainer>
      <PageHeader
        title="个人中心"
        actions={
          <Space>
            <Button onClick={() => { if (typeof window !== 'undefined') window.location.href = '/auth'; }} icon={<LockOutlined />}>
              重新授权
            </Button>
            <Button danger onClick={() => { if (typeof window !== 'undefined') window.location.href = '/logout'; }}>
              退出登录
            </Button>
          </Space>
        }
      />

      <Card style={{ maxWidth: 700, margin: '0 auto' }}>
        <div className={styles.header}>
          <Avatar size={80} icon={<UserOutlined />} className={styles.avatar} />
          <div className={styles.headerInfo}>
            <Title level={3} style={{ margin: 0, marginBottom: 'var(--spacing-2)' }}>
              {isEditing ? (
                <Form.Item name="accountName" rules={[{ required: true, message: '请输入账号名' }]}>
                  <Input size="large" style={{ width: 280 }} />
                </Form.Item>
              ) : (
                profileData.accountName
              )}
            </Title>
            <div className={styles.meta}>
              <span className={styles.tag}>
                {profileData.authorizationStatus === '已授权' ? '✅' : '❌'} {profileData.authorizationStatus}
              </span>
              <span className={styles.tag}>{profileData.accountType}</span>
            </div>
          </div>
        </div>

        <Divider style={{ margin: 'var(--spacing-6) 0' }} />

        <Form form={form} layout="vertical" onFinish={handleSave}>
          <Descriptions title="账号信息" column={1} size="middle" bordered>
            <Descriptions.Item label="账号 ID">
              {isEditing ? (
                <Input disabled style={{ width: '100%' }} placeholder="账号 ID 不可修改" />
              ) : (
                <code style={{ background: 'var(--color-bg-tertiary)', padding: 'var(--spacing-1) var(--spacing-2)', borderRadius: 'var(--radius-sm)' }}>
                  {userInfo.douyin_app_id}
                </code>
              )}
            </Descriptions.Item>

            <Descriptions.Item label="授权回调地址">
              {isEditing ? (
                <Input name="email" placeholder="请输入回调地址" />
              ) : (
                profileData.redirectUri
              )}
            </Descriptions.Item>

            <Descriptions.Item label="授权范围">
              {isEditing ? (
                <Input disabled placeholder="授权范围由后端管理" />
              ) : (
                <span className={styles.scope}>{profileData.scope}</span>
              )}
            </Descriptions.Item>

            <Descriptions.Item label="Access Token 过期时间">
              {profileData.accessTokenExpires}
            </Descriptions.Item>

            <Descriptions.Item label="刷新 Token">
              {isEditing ? (
                <Input.Password
                  name="refreshToken"
                  placeholder="刷新 Token 不可直接查看"
                  suffix={<LockOutlined />}
                />
              ) : (
                <span className={styles.masked}>••••••••••••</span>
              )}
            </Descriptions.Item>
          </Descriptions>

          <Divider style={{ margin: 'var(--spacing-6) 0' }} />

          <Space style={{ marginTop: 'var(--spacing-4)' }}>
            {isEditing ? (
              <>
                <Button type="primary" htmlType="submit" loading={saving} icon={<SaveOutlined />}>
                  保存
                </Button>
                <Button onClick={handleCancel} icon={<EditOutlined />}>
                  取消
                </Button>
              </>
            ) : (
              <Button type="primary" onClick={handleEdit} icon={<EditOutlined />}>
                编辑信息
              </Button>
            )}
          </Space>
        </Form>

        <Divider style={{ margin: 'var(--spacing-6) 0' }} />

        <Alert
          message="提示"
          description="个人中心功能正在完善中，当前展示的是抖音授权账号的基础信息。更多功能（修改密码、绑定手机/邮箱、通知设置等）需要后端 API 支持。"
          type="info"
          showIcon
          style={{ marginTop: 'var(--spacing-4)' }}
        />
      </Card>
    </PageContainer>
  );
};

export default Profile;