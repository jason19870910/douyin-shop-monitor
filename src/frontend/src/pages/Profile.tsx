import { useState, useMemo } from 'react';
import { DataTable, type DataTableColumn } from '@/components/common';
import { Form, Input, Button, Space, Typography } from 'antd';
import { formatDate } from '@/utils/formatters';
import { profileApi, type UserProfile } from '@/api/index';
import { message } from 'antd';

const Profile = () => {
  const [editing, setEditing] = useState(false);
  const [form] = Form.useForm();
  const [profile, setProfile] = useState<UserProfile | null>(null);

  // Load profile data
  const loadProfile = async () => {
    try {
      const data = await profileApi.getProfile();
      if (data) {
        setProfile(data);
        form.setFieldsValue({
          email: data.email || '',
          phone: data.phone || '',
        });
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
    }
  };

  const handleEdit = () => {
    setEditing(true);
  };

  const handleCancel = () => {
    setEditing(false);
    if (profile) {
      form.setFieldsValue({
        email: profile.email || '',
        phone: profile.phone || '',
      });
    }
  };

  const handleSave = async (values: { email: string; phone: string }) => {
    try {
      await profileApi.updateProfile(values);
      message.success('保存成功');
      setEditing(false);
      loadProfile();
    } catch (error) {
      message.error('保存失败');
      console.error('Failed to update profile:', error);
    }
  };

  const columns = useMemo<DataTableColumn<UserProfile>[]>(() => [
    { title: '用户ID', dataIndex: 'user_id', key: 'user_id', width: 120 },
    { title: '用户名', dataIndex: 'username', key: 'username', width: 150 },
    { title: '邮箱', dataIndex: 'email', key: 'email', width: 200 },
    { title: '手机号', dataIndex: 'phone', key: 'phone', width: 150 },
    { title: '角色', dataIndex: 'role', key: 'role', width: 100 },
    { title: '创建时间', dataIndex: 'create_time', key: 'create_time', width: 160, render: (value: unknown) => formatDate(value as string | null | undefined) },
    { title: '最后登录', dataIndex: 'last_login', key: 'last_login', width: 160, render: (value: unknown) => formatDate(value as string | null | undefined) },
  ], []);

  // Show editable form when editing, otherwise show DataTable
  if (editing && profile) {
    return (
      <Form form={form} layout="vertical" onFinish={handleSave} style={{ maxWidth: 500 }}>
        <Typography.Title level={3}>个人中心</Typography.Title>
        <Form.Item label="邮箱" name="email" rules={[{ type: 'email', message: '请输入有效的邮箱地址' }]}>
          <Input placeholder="请输入邮箱" />
        </Form.Item>
        <Form.Item label="手机号" name="phone" rules={[{ pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' }]}>
          <Input placeholder="请输入手机号" />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">保存</Button>
            <Button onClick={handleCancel}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    );
  }

  return (
    <DataTable<UserProfile>
      title="个人中心"
      queryKey={['profile']}
      queryFn={async () => {
        const profileData = await profileApi.getProfile();
        if (profileData) {
          setProfile(profileData);
        }
        return { items: profileData ? [profileData] : [], total: profileData ? 1 : 0 };
      }}
      columns={columns}
      rowKey="user_id"
      search={{ placeholder: '搜索用户信息...' }}
      extraActions={profile && !editing ? (
        <Button type="primary" onClick={handleEdit}>
          编辑资料
        </Button>
      ) : null}
    />
  );
};

export default Profile;