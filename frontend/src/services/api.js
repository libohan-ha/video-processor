import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 系统管理API
export const systemApi = {
  start: (configs) => api.post('/system/start', configs),
  stop: () => api.post('/system/stop'),
  getStatus: () => api.get('/system/status'),
};

// 摄像头管理API
export const cameraApi = {
  getStatus: (cameraId) => api.get(`/cameras/${cameraId}/status`),
  // WebSocket连接函数
  createStreamConnection: (cameraId) => {
    const ws = new WebSocket(`ws://localhost:8000/api/v1/cameras/${cameraId}/stream`);
    return ws;
  },
};

// 报警管理API
export const alertApi = {
  getAlerts: (timeRange, cameraId) => {
    const params = new URLSearchParams();
    if (timeRange.start_time) {
      params.append('start_time', timeRange.start_time);
    }
    if (timeRange.end_time) {
      params.append('end_time', timeRange.end_time);
    }
    if (cameraId) {
      params.append('camera_id', cameraId);
    }
    return api.get('/alerts', { params });
  },
  
  getSummary: (timeRange) => {
    const params = new URLSearchParams();
    if (timeRange.start_time) {
      params.append('start_time', timeRange.start_time);
    }
    if (timeRange.end_time) {
      params.append('end_time', timeRange.end_time);
    }
    return api.get('/alerts/summary', { params });
  },
  
  updateConfig: (config) => api.post('/alerts/config', config),
};
