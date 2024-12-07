import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  DatePicker,
  Select,
  Space,
  Tag,
  Image,
  Button,
  Row,
  Col,
} from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { alertApi } from '../services/api';

const { RangePicker } = DatePicker;

function AlertHistory() {
  const [loading, setLoading] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [timeRange, setTimeRange] = useState([
    dayjs().subtract(24, 'hour'),
    dayjs(),
  ]);
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });

  // 获取报警数据
  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const params = {
        start_time: timeRange[0].toISOString(),
        end_time: timeRange[1].toISOString(),
      };
      if (selectedCamera) {
        params.camera_id = selectedCamera;
      }
      const response = await alertApi.getAlerts(params);
      setAlerts(response.data);
      setPagination(prev => ({
        ...prev,
        total: response.data.length,
      }));
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [timeRange, selectedCamera]);

  // 表格列定义
  const columns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (text) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
      sorter: (a, b) => dayjs(a.timestamp).unix() - dayjs(b.timestamp).unix(),
    },
    {
      title: '摄像头',
      dataIndex: 'camera_id',
      key: 'camera_id',
      width: 100,
      filters: [
        { text: '摄像头 1', value: '1' },
        { text: '摄像头 2', value: '2' },
      ],
      onFilter: (value, record) => record.camera_id === value,
    },
    {
      title: '检测类型',
      dataIndex: ['detections', 0, 'class_name'],
      key: 'type',
      width: 120,
      render: (text) => (
        <Tag color={
          text.includes('火') || text.includes('烟')
            ? 'red'
            : text.includes('异常')
              ? 'orange'
              : 'blue'
        }>
          {text}
        </Tag>
      ),
    },
    {
      title: '置信度',
      dataIndex: ['detections', 0, 'confidence'],
      key: 'confidence',
      width: 100,
      render: (text) => `${(text * 100).toFixed(2)}%`,
      sorter: (a, b) => a.detections[0].confidence - b.detections[0].confidence,
    },
    {
      title: '截图',
      dataIndex: 'image_url',
      key: 'image',
      render: (text) => (
        <Image
          width={120}
          src={text}
          placeholder={
            <div style={{ background: '#f5f5f5', height: '67.5px', width: '120px' }} />
          }
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button type="link" size="small">
            详情
          </Button>
          <Button type="link" size="small">
            导出
          </Button>
        </Space>
      ),
    },
  ];

  // 处理时间范围变化
  const handleTimeRangeChange = (dates) => {
    setTimeRange(dates);
  };

  // 处理摄像头选择变化
  const handleCameraChange = (value) => {
    setSelectedCamera(value);
  };

  // 处理表格变化
  const handleTableChange = (newPagination, filters, sorter) => {
    setPagination(newPagination);
    // 可以根据需要处理排序和筛选
  };

  return (
    <Card>
      <Row gutter={24} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <RangePicker
            showTime
            value={timeRange}
            onChange={handleTimeRangeChange}
            style={{ width: '100%' }}
          />
        </Col>
        <Col span={8}>
          <Select
            placeholder="选择摄像头"
            allowClear
            style={{ width: '100%' }}
            onChange={handleCameraChange}
            value={selectedCamera}
          >
            <Select.Option value="1">摄像头 1</Select.Option>
            <Select.Option value="2">摄像头 2</Select.Option>
          </Select>
        </Col>
        <Col span={4}>
          <Button
            type="primary"
            icon={<SearchOutlined />}
            onClick={fetchAlerts}
            loading={loading}
            style={{ width: '100%' }}
          >
            查询
          </Button>
        </Col>
      </Row>

      <Table
        columns={columns}
        dataSource={alerts}
        rowKey="timestamp"
        pagination={pagination}
        onChange={handleTableChange}
        loading={loading}
        scroll={{ x: 1000 }}
      />
    </Card>
  );
}

export default AlertHistory;
