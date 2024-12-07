import React from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  VideoCameraOutlined,
  AlertOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import styled from 'styled-components';

const { Sider } = Layout;

const Logo = styled.div`
  height: 64px;
  padding: 16px;
  color: white;
  font-size: 18px;
  font-weight: bold;
  text-align: center;
  background: rgba(255, 255, 255, 0.1);
`;

const menuItems = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: '监控面板',
  },
  {
    key: '/camera',
    icon: <VideoCameraOutlined />,
    label: '摄像头管理',
    children: [
      {
        key: '/camera/1',
        label: '摄像头 1',
      },
      {
        key: '/camera/2',
        label: '摄像头 2',
      },
    ],
  },
  {
    key: '/alerts',
    icon: <AlertOutlined />,
    label: '报警历史',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: '系统设置',
  },
];

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  
  const handleMenuClick = ({ key }) => {
    navigate(key);
  };
  
  // 获取当前选中的菜单项
  const getSelectedKeys = () => {
    const path = location.pathname;
    if (path.startsWith('/camera/')) {
      return [path];
    }
    return [path];
  };
  
  return (
    <Sider width={200} theme="dark">
      <Logo>充电安全监控</Logo>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={getSelectedKeys()}
        items={menuItems}
        onClick={handleMenuClick}
      />
    </Sider>
  );
}

export default Sidebar;
