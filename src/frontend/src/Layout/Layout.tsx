import { useState, useEffect, Suspense, lazy } from 'react';
import { Layout as AntLayout, Menu, Button, Avatar, Dropdown, Space, message } from 'antd';
import { Link, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import {
  HomeOutlined, VideoCameraOutlined, UserOutlined, SafetyOutlined,
  ShopOutlined, DatabaseOutlined, FileTextOutlined, VideoCameraAddOutlined,
  PictureOutlined, UserAddOutlined, BellOutlined, MenuUnfoldOutlined,
  MenuFoldOutlined, SyncOutlined, ShoppingCartOutlined,
  SettingOutlined, BankOutlined, LineChartOutlined, CompassOutlined,
} from '@ant-design/icons';
import { syncApi, healthApi } from '@/api/index';
import { useApi } from '@/hooks/useApi';
import { formatDateTime } from '@/utils/formatters';
import styles from './Layout.module.css';

// 页面组件 - Home/Dashboard 直接导入，其余懒加载
import HomePage from '../pages/Home';
import DashboardPage from '../pages/Dashboard';
const VideosPage = lazy(() => import('../pages/Videos'));
const CreatorPage = lazy(() => import('../pages/Creator'));
const AuthPage = lazy(() => import('../pages/Auth'));
const ProductsPage = lazy(() => import('../pages/Products'));
const OrdersPage = lazy(() => import('../pages/Orders'));
const CompliancePage = lazy(() => import('../pages/Compliance'))
const VersionControlPage = lazy(() => import('../pages/VersionControl'));
const VideoEditPage = lazy(() => import('../pages/VideoEdit'));
const ImageEditPage = lazy(() => import('../pages/ImageEdit'));
const AccountPage = lazy(() => import('../pages/Account'));
const AlertsDouyinPage = lazy(() => import('../pages/AlertsDouyin'));
const AlertsDianPage = lazy(() => import('../pages/AlertsDian'));
const AlertHistoryPage = lazy(() => import('../pages/AlertHistory'));
const ProfilePage = lazy(() => import('../pages/Profile'));
const EarningsPage = lazy(() => import('../pages/Earnings'));
const EarningsTrendPage = lazy(() => import('../pages/EarningsTrend'));
const CompassPage = lazy(() => import('../pages/Compass'));

const { Sider, Content } = AntLayout;

const SIDEBAR_MENUS = {
  home: [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    { key: '/douyin', icon: <VideoCameraOutlined />, label: '抖音管理' },
    { key: '/dian', icon: <ShopOutlined />, label: '抖店管理' },
    { key: '/alerts', icon: <BellOutlined />, label: '告警设置' },
    { key: '/version', icon: <SettingOutlined />, label: '版本控制' },
  ],
  douyin: [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    { key: '/douyin/videos', icon: <VideoCameraOutlined />, label: '视频管理' },
    { key: '/douyin/creator', icon: <UserOutlined />, label: '创作者中心'},
    { key: '/douyin/earnings', icon: <BankOutlined />, label: '收益概览'},
    { key: '/douyin/earnings/trend', icon: <LineChartOutlined />, label: '收益趋势' },
    { key: '/auth', icon: <SafetyOutlined />, label: '授权状态' },
  ],
  dian: [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    { key: '/dian/products', icon: <ShoppingCartOutlined />, label: '商品管理' },
    { key: '/dian/orders', icon: <DatabaseOutlined />, label: '数据中心' },
    { key: '/dian/compliance', icon: <FileTextOutlined />, label: '合规管理' },
    { key: '/dian/video-edit', icon: <VideoCameraAddOutlined />, label: '视频素材' },
    { key: '/dian/image-edit', icon: <PictureOutlined />, label: '图片素材' },
    { key: '/dian/account', icon: <UserAddOutlined />, label: '账号管理' },
    { key: '/dian/compass', icon: <CompassOutlined />, label: '经营概况' },
  ],
  alerts: [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    { key: '/alerts/douyin', icon: <BellOutlined />, label: '抖音告警设置' },
    { key: '/alerts/dian', icon: <BellOutlined />, label: '抖店告警设置' },
    { key: '/alerts/history', icon: <BellOutlined />, label: '告警历史' },
  ],
  system: [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    { key: '/version', icon: <SettingOutlined />, label: '版本控制' },
  ],
};

function getSidebarType(pathname: string): keyof typeof SIDEBAR_MENUS {
  if (pathname.startsWith('/douyin') || pathname === '/auth') {
    return 'douyin';
  }
  if (pathname.startsWith('/dian')) {
    return 'dian';
  }
  if (pathname.startsWith('/version')) {
    return 'system';
  }
  if (pathname.startsWith('/alerts')) {
    return 'alerts';
  }
  return 'home';
}

export const AppLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [sidebarType, setSidebarType] = useState<keyof typeof SIDEBAR_MENUS>('home');

  const location = useLocation();
  const navigate = useNavigate();

  const { data: healthData, refetch: checkHealth } = useApi(async () => healthApi.check(), []);
  // Don't auto-call syncApi.manualSync on mount - only call on user action
  const [syncLoading, setSyncLoading] = useState(false);

  useEffect(() => {
    const type = getSidebarType(location.pathname);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSidebarType(type);
  }, [location.pathname]);

  // Update lastUpdate from health data
  // eslint-disable-next-line react-hooks/set-state-in-effect
  // useEffect(() => {
  //   if (healthData?.last_update) {
  //     setLastUpdate(healthData.last_update);
  //   }
  // }, [healthData]);

  const handleSync = async () => {
    setSyncLoading(true);
    let retries = 0;
    const maxRetries = 3;
    const baseDelay = 1000;

    while (retries <= maxRetries) {
      try {
        await syncApi.manualSync();
        checkHealth();
        message.success('数据同步成功');
        break; // Success, exit retry loop
      } catch (err) {
        retries++;
        if (retries > maxRetries) {
          message.error('同步失败，请稍后重试');
          if (import.meta.env.DEV) {
            console.error('Sync failed after retries:', err);
          }
          break;
        }
        // Exponential backoff
        const delay = baseDelay * 2 ** (retries - 1);
        if (import.meta.env.DEV) {
          console.info(`Sync retry ${retries}/${maxRetries} after ${delay}ms`);
        }
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }
    setSyncLoading(false);
  };

  const menuItems = SIDEBAR_MENUS[sidebarType] || SIDEBAR_MENUS.home;

  return (
    <AntLayout className={styles.layout} style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className={styles.sider}
        breakpoint="lg"
        collapsedWidth={80}
        onCollapse={(collapsed) => setCollapsed(collapsed)}
      >
        <div className={styles.siderContent}>
          <div className={styles.siderHeader}>
            <div className={styles.siderLogo}>
              <span className={styles.siderLogoIcon}>📊</span>
              {!collapsed && <span className={styles.siderLogoText}>抖音监控数据看板</span>}
            </div>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className={styles.siderCollapseBtn}
              style={{ width: '100%', justifyContent: collapsed ? 'center' : 'flex-start' }}
            />
          </div>

          <Menu
            theme="light"
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            className={styles.siderMenu}
          />

          <div className={styles.siderFooter}>
            <div className={styles.siderSyncArea}>
              <span className={styles.siderLastUpdate}>
                同步数据 {healthData?.last_update ? formatDateTime(healthData.last_update) : '暂无'}
              </span>
              <Button
                className={styles.siderSyncBtn}
                icon={<SyncOutlined />}
                onClick={handleSync}
                loading={syncLoading}
                type="primary"
                size={collapsed ? 'small' : 'middle'}
              >
                立即同步
              </Button>
            </div>
            <div className={styles.siderUserArea}>
              <Dropdown
                placement="bottomRight"
                menu={{
                  items: [
                    { key: 'profile', label: <Link to="/profile">个人中心</Link> },
                    {
                      key: 'logout',
                      label: '注销登出',
                      onClick: () => {
                        if (typeof window !== 'undefined') window.location.href = '/logout';
                      },
                    },
                  ],
                }}
              >
                <Space>
                  <Avatar size={28} icon={<UserOutlined />} />
                </Space>
              </Dropdown>
            </div>
          </div>
        </div>
      </Sider>

      <AntLayout className={`${styles.mainLayout} ${collapsed ? styles['sider-collapsed'] : ''}`}>
        <Content className={styles.content}>
          <Routes>
            {/* 首页/仪表盘 - 直接渲染避免重定向问题 */}
            <Route path="/" element={<HomePage />} />
            <Route path="/dashboard" element={<DashboardPage />} />

            {/* 抖音管理 */}
            <Route path="/douyin" element={<Navigate to="/douyin/videos" replace />} />
            <Route path="/douyin/videos" element={<VideosPage />} />
            <Route path="/douyin/creator" element={<CreatorPage />} />
            <Route path="/douyin/earnings" element={<EarningsPage />} />
            <Route path="/douyin/earnings/trend" element={<EarningsTrendPage />} />

            {/* 授权管理 */}
            <Route path="/auth" element={<AuthPage />} />

            {/* 抖店管理 */}
            <Route path="/dian" element={<Navigate to="/dian/products" replace />} />
            <Route path="/dian/products" element={<ProductsPage />} />
            <Route path="/dian/orders" element={<OrdersPage />} />
            <Route path="/dian/compliance" element={<CompliancePage />} />
            <Route path="/dian/video-edit" element={<VideoEditPage />} />
            <Route path="/dian/image-edit" element={<ImageEditPage />} />
            <Route path="/dian/account" element={<AccountPage />} />
            <Route path="/dian/compass" element={<CompassPage />} />
            <Route path="/version" element={<VersionControlPage />} />

            {/* 告警设置 */}
            <Route path="/alerts" element={<Navigate to="/alerts/douyin" replace />} />
            <Route path="/alerts/douyin" element={<AlertsDouyinPage />} />
            <Route path="/alerts/dian" element={<AlertsDianPage />} />
            <Route path="/alerts/history" element={<AlertHistoryPage />} />

            {/* 个人中心 */}
            <Route path="/profile" element={<ProfilePage />} />

            {/* 兜底 */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Content>
      </AntLayout>
    </AntLayout>
  );
};

export default function Layout() {
  return (
    <Suspense fallback={<div className="loading">加载中..</div>}>
      <AppLayout />
    </Suspense>
  );
}











