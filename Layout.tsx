import React, { useState, useEffect, Suspense, lazy } from 'react';
import { Layout as AntLayout, Menu, Button, Avatar, Dropdown, Space, Badge } from 'antd';
import { Link, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import {
  HomeOutlined,
  VideoCameraOutlined,
  UserOutlined,
  SafetyOutlined,
  ShopOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  VideoCameraAddOutlined,
  PictureOutlined,
  UserAddOutlined,
  BellOutlined,
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  SettingOutlined,
  SyncOutlined,
  UsergroupAddOutlined,
  ShoppingCartOutlined,
} from '@ant-design/icons';
import { syncApi, healthApi } from '@/api/index';
import { useApi } from '@/hooks/useApi';
import { formatDateTime } from '@/utils/formatters';
import styles from './Layout.module.css';

// 页面组件 - DashboardPage 同步导入（放在顶部确保被打包）
import DashboardPage from '../pages/Dashboard';
const VideosPage = lazy(() => import('../pages/Videos'));
const CreatorPage = lazy(() => import('../pages/Creator'));
const AuthPage = lazy(() => import('../pages/Auth'));
const ProductsPage = lazy(() => import('../pages/Products'));
const OrdersPage = lazy(() => import('../pages/Orders'));
const CompliancePage = lazy(() => import('../pages/Compliance'));
const VideoEditPage = lazy(() => import('../pages/VideoEdit'));
const ImageEditPage = lazy(() => import('../pages/ImageEdit'));
const AccountPage = lazy(() => import('../pages/Account'));
const AlertsDouyinPage = lazy(() => import('../pages/AlertsDouyin'));
const AlertsDianPage = lazy(() => import('../pages/AlertsDian'));
const ProfilePage = lazy(() => import('../pages/Profile'));

const { Sider, Content } = AntLayout;

const SIDEBAR_MENUS = {
  home: [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    { key: '/douyin', icon: <VideoCameraOutlined />, label: '抖音管理' },
    { key: '/dian', icon: <ShopOutlined />, label: '抖店管理' },
    { key: '/alerts', icon: <BellOutlined />, label: '告警设置' },
  ],
  douyin: [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    { key: '/douyin/videos', icon: <VideoCameraOutlined />, label: '视频管理' },
    { key: '/douyin/creator', icon: <UserOutlined />, label: '创作者中心' },
    { key: '/auth', icon: <SafetyOutlined />, label: '授权管理' },
  ],
  dian: [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    { key: '/dian/products', icon: <ShoppingCartOutlined />, label: '商品管理' },
    { key: '/dian/orders', icon: <DatabaseOutlined />, label: '数据中心' },
    { key: '/dian/compliance', icon: <FileTextOutlined />, label: '合规管理' },
    { key: '/dian/video-edit', icon: <VideoCameraAddOutlined />, label: '视频编辑' },
    { key: '/dian/image-edit', icon: <PictureOutlined />, label: '图片编辑' },
    { key: '/dian/account', icon: <UserAddOutlined />, label: '账号管理' },
  ],
  alerts: [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    { key: '/alerts/douyin', icon: <BellOutlined />, label: '抖音告警设置' },
    { key: '/alerts/dian', icon: <BellOutlined />, label: '抖店告警设置' },
  ],
};

function getSidebarType(pathname) {
  if (pathname.startsWith('/douyin') || pathname === '/auth') {
    return 'douyin';
  }
  if (pathname.startsWith('/dian')) {
    return 'dian';
  }
  if (pathname.startsWith('/alerts')) {
    return 'alerts';
  }
  return 'home';
}

export const AppLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [sidebarType, setSidebarType] = useState('home');
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  
  const location = useLocation();
  const navigate = useNavigate();
  
  const { data: healthData, refetch: checkHealth } = useApi(healthApi.check, []);
  // Don't auto-call syncApi.manualSync on mount - only call on user action
  const [syncLoading, setSyncLoading] = useState(false);

  useEffect(() => {
    const type = getSidebarType(location.pathname);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSidebarType(type);
  }, [location.pathname]);

  const handleSync = async () => {
    setSyncLoading(true);
    let retries = 0;
    const maxRetries = 3;
    const baseDelay = 1000;

    while (retries <= maxRetries) {
      try {
        await syncApi.manualSync();
        checkHealth();
        break; // Success, exit retry loop
      } catch (err) {
        retries++;
        if (retries > maxRetries) {
          // Production: replace with proper error reporting service
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

  const userMenu = (
    <Menu>
      <Menu.Item key="profile">
        <Link to="/profile">个人中心</Link>
      </Menu.Item>
      <Menu.Item key="logout" onClick={() => { if (typeof window !== 'undefined') window.location.href = '/logout'; }}>
        退出登录
      </Menu.Item>
    </Menu>
  );

  return (
    <AntLayout className={styles.layout} style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className={styles.sider}
        breakpoint="lg"
        collapsedWidth={80}
        onBreakpoint={(broken) => { }}
        onCollapse={(collapsed) => setCollapsed(collapsed)}
      >
        <div className={styles.siderContent}>
          <div className={styles.siderHeader}>
            <div className={styles.logo}>
              <span className={styles.logoIcon}>📊</span>
              {!collapsed && <span className={styles.logoText}>抖音电商数据监控</span>}
            </div>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className={styles.collapseBtn}
              style={{ width: '100%', justifyContent: collapsed ? 'center' : 'flex-start' }}
            />
          </div>
          
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            className={styles.menu}
          />
          
          <div className={styles.siderFooter}>
            <div className={styles.syncArea}>
              <span className={styles.lastUpdate}>
                最后更新: {lastUpdate ? formatDateTime(lastUpdate) : '未知'}
              </span>
              <Button
                className={styles.syncBtn}
                icon={<SyncOutlined />}
                onClick={handleSync}
                loading={syncLoading}
                type="primary"
                size={collapsed ? 'small' : 'middle'}
              >
                {!collapsed && '立即同步'}
              </Button>
            </div>
            <div className={styles.userArea}>
            <Dropdown
              placement="bottomRight"
              menu={{
                items: [
                  { key: 'profile', label: <Link to="/profile">个人中心</Link> },
                  { 
                    key: 'logout', 
                    label: '退出登录', 
                    onClick: () => { if (typeof window !== 'undefined') window.location.href = '/logout'; }
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
            <Route path="/" element={<DashboardPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            
            {/* 抖音管理 */}
            <Route path="/douyin" element={<Navigate to="/douyin/videos" replace />} />
            <Route path="/douyin/videos" element={<VideosPage />} />
            <Route path="/douyin/creator" element={<CreatorPage />} />
            
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
            
            {/* 告警设置 */}
            <Route path="/alerts" element={<Navigate to="/alerts/douyin" replace />} />
            <Route path="/alerts/douyin" element={<AlertsDouyinPage />} />
            <Route path="/alerts/dian" element={<AlertsDianPage />} />
            
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

// 默认导出
export default function Layout() {
  return (
    <Suspense fallback={<div className="loading">加载中...</div>}>
      <AppLayout />
    </Suspense>
  );
}