import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Table, Alert } from 'antd';
import { Line } from '@ant-design/plots';
import {
  AlertOutlined,
  VideoCameraOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import styled from 'styled-components';
import { systemApi, alertApi } from '../services/api';
import dayjs from 'dayjs';

const StyledCard = styled(Card)`
  margin-bottom: 24px;
`;

const AlertItem = styled.div`
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  &:last-child {
    border-bottom: none;
  }
`;

function Dashboard() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [alertSummary, setAlertSummary] = useState(null);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [alertTrend, setAlertTrend] = useState([]);

  useEffect(() => {
    // 获取系统状态
    const fetchSystemStatus = async () => {
      try {
        const response = await systemApi.getStatus();
        setSystemStatus(response.data);
      } catch (error) {
        console.error('Failed to fetch system status:', error);
      }
    };

    // 获取报警汇总
    const fetchAlertSummary = async () => {
      try {
        const timeRange = {
          start_time: dayjs().subtract(24, 'hour').toISOString(),
          end_time: dayjs().toISOString(),
        };
        const response = await alertApi.getSummary(timeRange);
        setAlertSummary(response.data);
      } catch (error) {
        console.error('Failed to fetch alert summary:', error);
      }
    };

    // 获取最近报警
    const fetchRecentAlerts = async () => {
      try {
        const timeRange = {
          start_time: dayjs().subtract(1, 'hour').toISOString(),
          end_time: dayjs().toISOString(),
        };
        const response = await alertApi.getAlerts(timeRange);
        setRecentAlerts(response.data);
      } catch (error) {
        console.error('Failed to fetch recent alerts:', error);
      }
    };

    // 获取报警趋势数据
    const fetchAlertTrend = async () => {
      try {
        const timeRange = {
          start_time: dayjs().subtract(7, 'day').toISOString(),
          end_time: dayjs().toISOString(),
        };
        const response = await alertApi.getAlerts(timeRange);
        
        // 处理数据以生成趋势图数据
        const trendData = response.data.reduce((acc, alert) => {
          const date = dayjs(alert.timestamp).format('YYYY-MM-DD');
          acc[date] = (acc[date] || 0) + 1;
          return acc;
        }, {});
        
        const data = Object.entries(trendData).map(([date, count]) => ({
          date,
          count,
        }));
        
        setAlertTrend(data);
      } catch (error) {
        console.error('Failed to fetch alert trend:', error);
      }
    };

    // 定期刷新数据
    const fetchData = () => {
      fetchSystemStatus();
      fetchAlertSummary();
      fetchRecentAlerts();
      fetchAlertTrend();
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // 每30秒刷新一次

    return () => clearInterval(interval);
  }, []);

  // 趋势图配置
  const trendConfig = {
    data: alertTrend,
    xField: 'date',
    yField: 'count',
    smooth: true,
    point: {
      size: 5,
      shape: 'diamond',
    },
  };

  // 最近报警表格列定义
  const columns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '摄像头',
      dataIndex: 'camera_id',
      key: 'camera_id',
    },
    {
      title: '类型',
      dataIndex: ['detections', 0, 'class_name'],
      key: 'type',
    },
    {
      title: '置信度',
      dataIndex: ['detections', 0, 'confidence'],
      key: 'confidence',
      render: (text) => `${(text * 100).toFixed(2)}%`,
    },
  ];

  return (
    <div>
      <Row gutter={24}>
        <Col span={8}>
          <StyledCard>
            <Statistic
              title="系统状态"
              value={systemStatus?.is_running ? '运行中' : '已停止'}
              prefix={<CheckCircleOutlined style={{ color: systemStatus?.is_running ? '#52c41a' : '#ff4d4f' }} />}
            />
          </StyledCard>
        </Col>
        <Col span={8}>
          <StyledCard>
            <Statistic
              title="活跃摄像头"
              value={systemStatus?.active_cameras?.length || 0}
              prefix={<VideoCameraOutlined />}
            />
          </StyledCard>
        </Col>
        <Col span={8}>
          <StyledCard>
            <Statistic
              title="今日报警"
              value={alertSummary?.total_alerts || 0}
              prefix={<AlertOutlined />}
            />
          </StyledCard>
        </Col>
      </Row>

      <Row gutter={24}>
        <Col span={16}>
          <StyledCard title="报警趋势">
            <Line {...trendConfig} />
          </StyledCard>
        </Col>
        <Col span={8}>
          <StyledCard title="实时报警" style={{ height: '400px', overflow: 'auto' }}>
            {recentAlerts.map((alert) => (
              <AlertItem key={alert.timestamp}>
                <Alert
                  message={alert.detections[0].class_name}
                  description={`摄像头 ${alert.camera_id} - ${dayjs(alert.timestamp).format('HH:mm:ss')}`}
                  type="warning"
                  showIcon
                />
              </AlertItem>
            ))}
          </StyledCard>
        </Col>
      </Row>

      <StyledCard title="最近报警记录">
        <Table
          columns={columns}
          dataSource={recentAlerts}
          rowKey="timestamp"
          pagination={{ pageSize: 5 }}
        />
      </StyledCard>
    </div>
  );
}

export default Dashboard;
