import React, { useState, useEffect } from 'react';
import { Card, Button, message, Divider, Space } from 'antd';
import { ReloadOutlined, QrcodeOutlined, LoginOutlined, LogoutOutlined } from '@ant-design/icons';
import { authApi, healthApi, setAuthToken, type AuthStatus, type HealthResponse } from '@/api/index';
import { useApi } from '@/hooks/useApi';
import { PageContainer, PageHeader } from '@/components/layout';
import styles from './Auth.module.css';

const Auth = () => {
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const { data: healthData, refetch: checkHealth } = useApi<HealthResponse>(healthApi.check, []);
  const { data: authData, loading: authLoading, refetch: refetchAuth } = useApi<AuthStatus>(authApi.getStatus, []);

  const authStatus = authData?.authorized ? 'authorized' : authLoading ? 'checking' : 'unauthorized';
  const authInfo = authData;
  
  // 当授权信息返回且包含 access_token 时，保存到本地存储供后续请求使用
  useEffect(() => {
    if (authInfo?.authorized && authInfo?.access_token) {
      setAuthToken(authInfo.access_token);
    }
  }, [authInfo]);

  const displayAuthStatus = authStatus as 'authorized' | 'checking' | 'unauthorized' | 'error';

  const checkAuth = async () => {
    refetchAuth();
  };

  const handleLogin = async () => {
    try {
      const res = await authApi.login();
      if (res?.auth_url && typeof window !== 'undefined') {
        window.location.href = res.auth_url;
      }
    } catch (_err) {
      message.error('授权失败');
    }
  };

  const handleLogout = async () => {
    try {
      await authApi.logout();
      message.success('已撤销授权');
      checkAuth();
    } catch (err) {
      message.error('撤销授权失败');
    }
  };

  const handleRefreshQr = async () => {
    try {
      const res = await authApi.getQrCode();
      if (res?.qr_code) {
        setQrCode(res.qr_code);
      }
    } catch (_err) {
      message.error('获取二维码失败');
    }
  };

  return (
    <PageContainer>
      <PageHeader
        title="授权管理"
        actions={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={checkAuth} loading={displayAuthStatus === 'checking'}>刷新状态</Button>
            <Button icon={<QrcodeOutlined />} onClick={handleRefreshQr}>刷新二维码</Button>
          </Space>
        }
      />

      <Card className={styles.authCard}>
        <div className={styles.authStatus}>
          <div className={`${styles.statusIndicator} ${displayAuthStatus}`}>
            {displayAuthStatus === 'authorized' && '✅ 已授权'}
            {displayAuthStatus === 'unauthorized' && '❌ 未授权'}
            {displayAuthStatus === 'checking' && '⏳ 检查中...'}
            {displayAuthStatus === 'error' && '⚠️ 检查失败'}
          </div>
          <div className={styles.statusActions}>
            {displayAuthStatus === 'unauthorized' && (
              <Button type="primary" icon={<LoginOutlined />} onClick={handleLogin} size="large">
                授权登录
              </Button>
            )}
            {displayAuthStatus === 'authorized' && (
              <Button danger icon={<LogoutOutlined />} onClick={handleLogout} size="large">
                撤销授权
              </Button>
            )}
          </div>
        </div>

        <Divider>授权信息</Divider>
        <Card className={styles.authInfo}>
          {authInfo && (
            <>
              <p><strong>App ID:</strong> {authInfo.douyin_app_id || '-'}</p>
              <p><strong>Access Token:</strong> {authInfo.access_token ? authInfo.access_token.substring(0, 20) + '...' : '-'}</p>
              <p><strong>过期时间:</strong> {authInfo.expires_at ? new Date(authInfo.expires_at).toLocaleString() : '-'}</p>
              <p><strong>权限范围:</strong> {authInfo.scope?.join(', ') || '-'}</p>
            </>
          )}
          {!authInfo && <p className={styles.noInfo}>暂无授权信息</p>}
        </Card>

        <Divider>扫码授权</Divider>
        <div className={styles.qrSection}>
          {qrCode ? (
            <img src={qrCode} alt="授权二维码" className={styles.qrCode} />
          ) : (
            <div className={styles.qrPlaceholder}>加载二维码中...</div>
          )}
          <p className={styles.qrTip}>使用抖音APP扫码授权</p>
          <Button icon={<QrcodeOutlined />} onClick={handleRefreshQr}>刷新二维码</Button>
        </div>
      </Card>
    </PageContainer>
  );
};

export default Auth;