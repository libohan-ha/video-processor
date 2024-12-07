# 电动车充电安全监控系统 API

## 概述

本API提供了电动车充电安全监控系统的后端接口，支持实时视频流处理、异常行为检测、火灾隐患识别等功能。

## API端点

### 系统管理

#### POST /api/v1/system/start
启动监控系统
- 请求体：摄像头配置列表
- 响应：系统启动状态

#### POST /api/v1/system/stop
停止监控系统
- 响应：系统停止状态

#### GET /api/v1/system/status
获取系统状态
- 响应：系统运行状态信息

### 摄像头管理

#### GET /api/v1/cameras/{camera_id}/status
获取摄像头状态
- 参数：camera_id (路径参数)
- 响应：摄像头状态信息

#### WebSocket /api/v1/cameras/{camera_id}/stream
实时视频流
- 参数：camera_id (路径参数)
- 响应：视频帧和检测结果的WebSocket流

### 报警管理

#### GET /api/v1/alerts
获取报警历史
- 参数：
  - time_range (查询参数)
  - camera_id (可选查询参数)
- 响应：报警记录列表

#### GET /api/v1/alerts/summary
获取报警汇总信息
- 参数：time_range (查询参数)
- 响应：报警统计信息

#### POST /api/v1/alerts/config
更新报警配置
- 请求体：报警配置信息
- 响应：配置更新状态

## 数据模型

### CameraConfig
```python
{
    "id": "string",
    "source": "string",
    "name": "string",
    "location": "string"
}
```

### DetectionResult
```python
{
    "timestamp": "datetime",
    "camera_id": "string",
    "detections": [
        {
            "class_name": "string",
            "confidence": float,
            "heatmap": [[float]]
        }
    ],
    "raw_probabilities": {
        "class_name": float
    },
    "frame_info": {
        "width": int,
        "height": int
    }
}
```

### AlertConfig
```python
{
    "threshold": float,
    "notification_methods": ["string"]
}
```

## 使用示例

### 启动系统
```python
import requests

cameras = [
    {
        "id": "cam1",
        "source": "0",
        "name": "前门摄像头",
        "location": "充电区域1"
    }
]

response = requests.post(
    "http://localhost:8000/api/v1/system/start",
    json=cameras
)
print(response.json())
```

### 获取实时视频流
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/cameras/cam1/stream');

ws.onmessage = (event) => {
    if (event.data instanceof Blob) {
        // 处理视频帧
        const frame = URL.createObjectURL(event.data);
        displayFrame(frame);
    } else {
        // 处理检测结果
        const detection = JSON.parse(event.data);
        handleDetection(detection);
    }
};
```

## 部署说明

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 启动服务器
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

3. 访问API文档
```
http://localhost:8000/docs
```

## 注意事项

1. 在生产环境中，请确保：
   - 配置适当的CORS策略
   - 启用身份验证和授权
   - 使用HTTPS
   - 限制WebSocket连接数
   - 配置适当的日志级别

2. 性能优化：
   - 根据服务器配置调整worker数量
   - 配置适当的帧率和分辨率
   - 使用缓存减少数据库查询
   - 实现数据清理策略
