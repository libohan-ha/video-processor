import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Row, Col, Descriptions, Badge, Alert } from 'antd';
import styled from 'styled-components';
import { cameraApi } from '../services/api';
import dayjs from 'dayjs';

const VideoContainer = styled.div`
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 宽高比 */
  background: #000;
  border-radius: 4px;
  overflow: hidden;
`;

const Video = styled.canvas`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
`;

const DetectionOverlay = styled.div`
  position: absolute;
  top: 16px;
  left: 16px;
  right: 16px;
  z-index: 1;
`;

function CameraView() {
  const { id } = useParams();
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const [status, setStatus] = useState(null);
  const [latestDetection, setLatestDetection] = useState(null);

  useEffect(() => {
    // 获取摄像头状态
    const fetchStatus = async () => {
      try {
        const response = await cameraApi.getStatus(id);
        setStatus(response.data);
      } catch (error) {
        console.error('Failed to fetch camera status:', error);
      }
    };

    fetchStatus();
    const statusInterval = setInterval(fetchStatus, 5000);

    // 建立WebSocket连接
    const setupWebSocket = () => {
      wsRef.current = cameraApi.createStreamConnection(id);

      wsRef.current.onmessage = (event) => {
        if (event.data instanceof Blob) {
          // 处理视频帧
          const blob = event.data;
          const reader = new FileReader();
          reader.onload = () => {
            const img = new Image();
            img.onload = () => {
              const canvas = canvasRef.current;
              const ctx = canvas.getContext('2d');
              canvas.width = img.width;
              canvas.height = img.height;
              ctx.drawImage(img, 0, 0);
            };
            img.src = reader.result;
          };
          reader.readAsDataURL(blob);
        } else {
          // 处理检测结果
          const detection = JSON.parse(event.data);
          setLatestDetection(detection);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      wsRef.current.onclose = () => {
        // 断线重连
        setTimeout(setupWebSocket, 5000);
      };
    };

    setupWebSocket();

    return () => {
      clearInterval(statusInterval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [id]);

  // 渲染检测结果
  const renderDetections = () => {
    if (!latestDetection?.detections?.length) {
      return null;
    }

    return latestDetection.detections.map((detection, index) => (
      <Alert
        key={index}
        message={detection.class_name}
        description={`置信度: ${(detection.confidence * 100).toFixed(2)}%`}
        type={detection.confidence > 0.8 ? 'error' : 'warning'}
        style={{ marginBottom: 8 }}
        showIcon
      />
    ));
  };

  return (
    <div>
      <Row gutter={24}>
        <Col span={16}>
          <Card title={`摄像头 ${id} 实时画面`}>
            <VideoContainer>
              <Video ref={canvasRef} />
              <DetectionOverlay>
                {renderDetections()}
              </DetectionOverlay>
            </VideoContainer>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="摄像头信息">
            <Descriptions column={1}>
              <Descriptions.Item label="状态">
                <Badge
                  status={status?.is_active ? 'success' : 'error'}
                  text={status?.is_active ? '在线' : '离线'}
                />
              </Descriptions.Item>
              <Descriptions.Item label="分辨率">
                {status?.frame_width} x {status?.frame_height}
              </Descriptions.Item>
              <Descriptions.Item label="帧率">
                {status?.fps} FPS
              </Descriptions.Item>
              <Descriptions.Item label="最后更新">
                {status?.latest_detection?.timestamp
                  ? dayjs(status.latest_detection.timestamp).format('YYYY-MM-DD HH:mm:ss')
                  : '-'}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          <Card title="实时检测结果" style={{ marginTop: 24 }}>
            {latestDetection?.detections?.length ? (
              latestDetection.detections.map((detection, index) => (
                <Descriptions key={index} column={1} style={{ marginBottom: 16 }}>
                  <Descriptions.Item label="类型">
                    {detection.class_name}
                  </Descriptions.Item>
                  <Descriptions.Item label="置信度">
                    {(detection.confidence * 100).toFixed(2)}%
                  </Descriptions.Item>
                  <Descriptions.Item label="检测时间">
                    {dayjs(latestDetection.timestamp).format('HH:mm:ss')}
                  </Descriptions.Item>
                </Descriptions>
              ))
            ) : (
              <Alert message="暂无异常" type="info" showIcon />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default CameraView;
