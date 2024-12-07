import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Switch,
  Button,
  message,
  Tabs,
  Select,
  Space,
  Divider,
} from 'antd';
import { systemApi, alertApi } from '../services/api';

const { TabPane } = Tabs;
const { Option } = Select;

function Settings() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);

  // 获取系统状态和配置
  useEffect(() => {
    const fetchSystemStatus = async () => {
      try {
        const response = await systemApi.getStatus();
        setSystemStatus(response.data);
        form.setFieldsValue({
          ...response.data.config,
        });
      } catch (error) {
        console.error('Failed to fetch system status:', error);
        message.error('获取系统配置失败');
      }
    };

    fetchSystemStatus();
  }, [form]);

  // 保存系统配置
  const handleSaveConfig = async (values) => {
    setLoading(true);
    try {
      await systemApi.start(values);
      message.success('配置已保存');
    } catch (error) {
      console.error('Failed to save config:', error);
      message.error('保存配置失败');
    } finally {
      setLoading(false);
    }
  };

  // 保存报警配置
  const handleSaveAlertConfig = async (values) => {
    setLoading(true);
    try {
      await alertApi.updateConfig(values);
      message.success('报警配置已保存');
    } catch (error) {
      console.error('Failed to save alert config:', error);
      message.error('保存报警配置失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <Tabs defaultActiveKey="system">
        <TabPane tab="系统设置" key="system">
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSaveConfig}
          >
            <Form.Item
              label="系统状态"
              name="is_running"
              valuePropName="checked"
            >
              <Switch
                checkedChildren="运行中"
                unCheckedChildren="已停止"
              />
            </Form.Item>

            <Divider orientation="left">摄像头设置</Divider>

            <Form.List name="cameras">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                      <Form.Item
                        {...restField}
                        name={[name, 'id']}
                        rules={[{ required: true, message: '请输入摄像头ID' }]}
                      >
                        <Input placeholder="摄像头ID" />
                      </Form.Item>
                      <Form.Item
                        {...restField}
                        name={[name, 'url']}
                        rules={[{ required: true, message: '请输入摄像头URL' }]}
                      >
                        <Input placeholder="RTSP URL" style={{ width: 300 }} />
                      </Form.Item>
                      <Button onClick={() => remove(name)}>删除</Button>
                    </Space>
                  ))}
                  <Form.Item>
                    <Button type="dashed" onClick={() => add()} block>
                      添加摄像头
                    </Button>
                  </Form.Item>
                </>
              )}
            </Form.List>

            <Divider orientation="left">AI模型设置</Divider>

            <Form.Item
              label="检测阈值"
              name={['model', 'confidence_threshold']}
              rules={[{ required: true, message: '请输入检测阈值' }]}
            >
              <InputNumber
                min={0}
                max={1}
                step={0.01}
                style={{ width: 200 }}
              />
            </Form.Item>

            <Form.Item
              label="检测间隔 (ms)"
              name={['model', 'detection_interval']}
              rules={[{ required: true, message: '请输入检测间隔' }]}
            >
              <InputNumber
                min={100}
                max={5000}
                step={100}
                style={{ width: 200 }}
              />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading}>
                保存系统设置
              </Button>
            </Form.Item>
          </Form>
        </TabPane>

        <TabPane tab="报警设置" key="alert">
          <Form
            layout="vertical"
            onFinish={handleSaveAlertConfig}
          >
            <Form.Item
              label="报警类型"
              name="alert_types"
              rules={[{ required: true, message: '请选择报警类型' }]}
            >
              <Select mode="multiple" style={{ width: '100%' }}>
                <Option value="fire">火灾</Option>
                <Option value="smoke">烟雾</Option>
                <Option value="unauthorized">未授权充电</Option>
                <Option value="cable_damage">线缆损坏</Option>
              </Select>
            </Form.Item>

            <Form.Item
              label="报警阈值"
              name="alert_threshold"
              rules={[{ required: true, message: '请输入报警阈值' }]}
            >
              <InputNumber
                min={0}
                max={1}
                step={0.01}
                style={{ width: 200 }}
              />
            </Form.Item>

            <Form.Item
              label="报警间隔 (秒)"
              name="alert_interval"
              rules={[{ required: true, message: '请输入报警间隔' }]}
            >
              <InputNumber
                min={1}
                max={3600}
                style={{ width: 200 }}
              />
            </Form.Item>

            <Form.Item
              label="通知方式"
              name="notification_methods"
              rules={[{ required: true, message: '请选择通知方式' }]}
            >
              <Select mode="multiple" style={{ width: '100%' }}>
                <Option value="email">邮件</Option>
                <Option value="sms">短信</Option>
                <Option value="webhook">Webhook</Option>
              </Select>
            </Form.Item>

            <Form.Item
              label="通知接收人"
              name="notification_recipients"
            >
              <Select mode="tags" style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading}>
                保存报警设置
              </Button>
            </Form.Item>
          </Form>
        </TabPane>
      </Tabs>
    </Card>
  );
}

export default Settings;
