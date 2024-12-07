"""
API数据模型定义
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class CameraConfig(BaseModel):
    """摄像头配置"""
    id: str = Field(..., description="摄像头ID")
    source: str = Field(..., description="视频源（摄像头索引或URL）")
    name: Optional[str] = Field(None, description="摄像头名称")
    location: Optional[str] = Field(None, description="安装位置")

class Detection(BaseModel):
    """检测结果"""
    class_name: str = Field(..., description="检测类别")
    confidence: float = Field(..., description="置信度")
    heatmap: Optional[List[List[float]]] = Field(None, description="热力图数据")

class DetectionResult(BaseModel):
    """完整的检测结果"""
    timestamp: datetime = Field(..., description="检测时间")
    camera_id: str = Field(..., description="摄像头ID")
    detections: List[Detection] = Field(..., description="检测结果列表")
    raw_probabilities: Dict[str, float] = Field(..., description="原始概率分布")
    frame_info: Dict[str, int] = Field(..., description="帧信息")

class AlertConfig(BaseModel):
    """报警配置"""
    threshold: float = Field(0.8, description="报警阈值")
    notification_methods: List[str] = Field(
        default=["log"],
        description="通知方式（log, email, sms, webhook）"
    )

class CameraStatus(BaseModel):
    """摄像头状态"""
    camera_id: str = Field(..., description="摄像头ID")
    is_active: bool = Field(..., description="是否活跃")
    latest_detection: Optional[DetectionResult] = Field(None, description="最新检测结果")
    frame_width: Optional[int] = Field(None, description="帧宽度")
    frame_height: Optional[int] = Field(None, description="帧高度")
    fps: Optional[int] = Field(None, description="帧率")

class SystemStatus(BaseModel):
    """系统状态"""
    is_running: bool = Field(..., description="系统是否运行中")
    active_cameras: List[str] = Field(..., description="活跃摄像头ID列表")
    total_alerts: int = Field(..., description="报警总数")
    start_time: datetime = Field(..., description="系统启动时间")

class TimeRange(BaseModel):
    """时间范围"""
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")

class AlertSummary(BaseModel):
    """报警汇总"""
    total_alerts: int = Field(..., description="报警总数")
    alert_types: Dict[str, int] = Field(..., description="各类型报警数量")
    time_range: TimeRange = Field(..., description="时间范围")
