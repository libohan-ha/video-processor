"""
API路由定义
"""
from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket
from typing import List, Optional
from datetime import datetime
import asyncio
import json

from .models import (
    CameraConfig, Detection, DetectionResult, AlertConfig,
    CameraStatus, SystemStatus, TimeRange, AlertSummary
)
from ..core.monitor_manager import MonitorManager

# 创建路由器
router = APIRouter()

# 全局监控管理器实例
monitor_manager: Optional[MonitorManager] = None

def get_monitor_manager() -> MonitorManager:
    """获取监控管理器实例"""
    if monitor_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Monitor manager not initialized"
        )
    return monitor_manager

# 系统控制路由
@router.post("/system/start")
async def start_system(configs: List[CameraConfig]):
    """启动监控系统"""
    global monitor_manager
    
    if monitor_manager and monitor_manager.is_running:
        raise HTTPException(
            status_code=400,
            detail="System is already running"
        )
    
    try:
        camera_configs = [config.dict() for config in configs]
        monitor_manager = MonitorManager(
            camera_configs=camera_configs,
            save_dir="./data/alerts"
        )
        monitor_manager.start_monitoring()
        return {"status": "success", "message": "System started successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start system: {str(e)}"
        )

@router.post("/system/stop")
async def stop_system(manager: MonitorManager = Depends(get_monitor_manager)):
    """停止监控系统"""
    try:
        manager.stop_monitoring()
        return {"status": "success", "message": "System stopped successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop system: {str(e)}"
        )

@router.get("/system/status", response_model=SystemStatus)
async def get_system_status(manager: MonitorManager = Depends(get_monitor_manager)):
    """获取系统状态"""
    return {
        "is_running": manager.is_running,
        "active_cameras": list(manager.processors.keys()),
        "total_alerts": manager.alerts_queue.qsize(),
        "start_time": datetime.now()  # TODO: 记录实际启动时间
    }

# 摄像头管理路由
@router.get("/cameras/{camera_id}/status", response_model=CameraStatus)
async def get_camera_status(
    camera_id: str,
    manager: MonitorManager = Depends(get_monitor_manager)
):
    """获取摄像头状态"""
    try:
        return manager.get_camera_status(camera_id)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

@router.websocket("/cameras/{camera_id}/stream")
async def stream_camera(
    websocket: WebSocket,
    camera_id: str,
    manager: MonitorManager = Depends(get_monitor_manager)
):
    """WebSocket视频流"""
    await websocket.accept()
    
    try:
        processor = manager.processors[camera_id]
    except KeyError:
        await websocket.close(code=1000, reason=f"Camera {camera_id} not found")
        return
    
    try:
        while True:
            # 获取最新帧和检测结果
            frame, detection = processor.get_latest_frame()
            if frame is not None and detection is not None:
                # 将帧编码为JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                # 发送帧和检测结果
                await websocket.send_bytes(buffer.tobytes())
                await websocket.send_json(detection)
            
            await asyncio.sleep(0.1)  # 控制帧率
    except Exception as e:
        await websocket.close(code=1000, reason=str(e))

# 报警管理路由
@router.get("/alerts", response_model=List[DetectionResult])
async def get_alerts(
    time_range: TimeRange,
    camera_id: Optional[str] = None,
    manager: MonitorManager = Depends(get_monitor_manager)
):
    """获取报警历史"""
    try:
        return manager.get_alerts_history(
            start_time=time_range.start_time.isoformat() if time_range.start_time else None,
            end_time=time_range.end_time.isoformat() if time_range.end_time else None,
            camera_id=camera_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

@router.get("/alerts/summary", response_model=AlertSummary)
async def get_alerts_summary(
    time_range: TimeRange,
    manager: MonitorManager = Depends(get_monitor_manager)
):
    """获取报警汇总信息"""
    alerts = await get_alerts(time_range, manager=manager)
    
    # 统计各类型报警数量
    alert_types = {}
    for alert in alerts:
        for detection in alert.detections:
            alert_types[detection.class_name] = \
                alert_types.get(detection.class_name, 0) + 1
    
    return {
        "total_alerts": len(alerts),
        "alert_types": alert_types,
        "time_range": time_range
    }

@router.post("/alerts/config")
async def update_alert_config(
    config: AlertConfig,
    manager: MonitorManager = Depends(get_monitor_manager)
):
    """更新报警配置"""
    manager.alert_threshold = config.threshold
    # TODO: 实现通知方式配置
    return {"status": "success", "message": "Alert config updated successfully"}
