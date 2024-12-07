"""
实时监控管理器
"""
import threading
import queue
import time
from typing import Dict, List, Optional
import logging
from datetime import datetime
import json
from pathlib import Path

from .video_processor import VideoProcessor
from .anomaly_detector import AnomalyDetector
from .fire_hazard_detector import FireHazardDetector

class MonitorManager:
    def __init__(self,
                 camera_configs: List[Dict],
                 save_dir: str,
                 alert_threshold: float = 0.8,
                 max_history_size: int = 10000):
        """
        监控管理器
        
        Args:
            camera_configs: 摄像头配置列表
            save_dir: 结果保存目录
            alert_threshold: 报警阈值
            max_history_size: 最大历史记录数量
        """
        self.camera_configs = camera_configs
        self.save_dir = Path(save_dir)
        self.alert_threshold = alert_threshold
        self.max_history_size = max_history_size
        
        # 创建保存目录
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化模型
        self.anomaly_detector = AnomalyDetector()
        self.fire_hazard_detector = FireHazardDetector()
        
        # 初始化视频处理器
        self.processors = {}
        self.alerts_queue = queue.Queue()
        
        # 初始化日志
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # 初始化状态
        self.is_running = False
        self.alert_thread = None

    def start_monitoring(self):
        """
        启动监控
        """
        if self.is_running:
            return
            
        self.is_running = True
        
        # 启动所有视频处理器
        for config in self.camera_configs:
            camera_id = config['id']
            source = config['source']
            
            # 创建视频处理器
            processor = VideoProcessor(
                model=self.anomaly_detector,
                source=source,
                buffer_size=30,
                detection_interval=0.5
            )
            
            try:
                processor.start()
                self.processors[camera_id] = processor
                self.logger.info(f"摄像头 {camera_id} 已启动")
            except Exception as e:
                self.logger.error(f"摄像头 {camera_id} 启动失败: {str(e)}")
        
        # 启动报警处理线程
        self.alert_thread = threading.Thread(
            target=self._alert_processing_thread,
            daemon=True
        )
        self.alert_thread.start()
        
        self.logger.info("监控系统已启动")

    def stop_monitoring(self):
        """
        停止监控
        """
        if not self.is_running:
            return
            
        self.is_running = False
        
        # 停止所有视频处理器
        for camera_id, processor in self.processors.items():
            try:
                processor.stop()
                self.logger.info(f"摄像头 {camera_id} 已停止")
            except Exception as e:
                self.logger.error(f"摄像头 {camera_id} 停止失败: {str(e)}")
        
        # 等待报警处理线程结束
        if self.alert_thread:
            self.alert_thread.join()
        
        self.logger.info("监控系统已停止")

    def _alert_processing_thread(self):
        """
        报警处理线程
        """
        while self.is_running:
            try:
                alert = self.alerts_queue.get(timeout=1.0)
            except queue.Empty:
                continue
            
            # 处理报警信息
            self._handle_alert(alert)

    def _handle_alert(self, alert: Dict):
        """
        处理报警信息
        
        Args:
            alert: 报警信息字典
        """
        # 记录报警信息
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        alert_file = self.save_dir / f"alert_{timestamp}.json"
        
        with open(alert_file, 'w') as f:
            json.dump(alert, f, indent=2)
        
        # 根据报警类型和置信度决定通知方式
        if self._should_trigger_immediate_alert(alert):
            self._send_immediate_alert(alert)
        else:
            self._log_alert(alert)

    def _should_trigger_immediate_alert(self, alert: Dict) -> bool:
        """
        判断是否需要立即报警
        
        Args:
            alert: 报警信息
            
        Returns:
            是否需要立即报警
        """
        # 检查是否存在高置信度的危险检测结果
        for detection in alert.get('detections', []):
            if detection['confidence'] > self.alert_threshold:
                if detection['class_name'] in ['smoke', 'spark', 'overheat',
                                             'unauthorized_charging', 'cable_damage']:
                    return True
        return False

    def _send_immediate_alert(self, alert: Dict):
        """
        发送即时报警
        
        Args:
            alert: 报警信息
        """
        # TODO: 实现具体的报警方式，如：
        # - 发送短信
        # - 发送邮件
        # - 触发声光报警
        # - 通知相关人员
        self.logger.warning(f"紧急报警: {alert}")

    def _log_alert(self, alert: Dict):
        """
        记录普通报警信息
        
        Args:
            alert: 报警信息
        """
        self.logger.info(f"普通报警: {alert}")

    def get_camera_status(self, camera_id: str) -> Dict:
        """
        获取摄像头状态
        
        Args:
            camera_id: 摄像头ID
            
        Returns:
            摄像头状态信息
        """
        if camera_id not in self.processors:
            raise ValueError(f"未找到摄像头: {camera_id}")
            
        processor = self.processors[camera_id]
        latest_frame, latest_detection = processor.get_latest_frame()
        
        return {
            'camera_id': camera_id,
            'is_active': processor.is_running,
            'latest_detection': latest_detection,
            'frame_width': processor.frame_width,
            'frame_height': processor.frame_height,
            'fps': processor.fps
        }

    def get_alerts_history(self,
                          start_time: Optional[str] = None,
                          end_time: Optional[str] = None,
                          camera_id: Optional[str] = None) -> List[Dict]:
        """
        获取报警历史记录
        
        Args:
            start_time: 开始时间（ISO格式）
            end_time: 结束时间（ISO格式）
            camera_id: 摄像头ID
            
        Returns:
            报警记录列表
        """
        if camera_id and camera_id not in self.processors:
            raise ValueError(f"未找到摄像头: {camera_id}")
            
        if camera_id:
            return self.processors[camera_id].get_detection_history(
                start_time, end_time
            )
            
        # 合并所有摄像头的历史记录
        all_history = []
        for processor in self.processors.values():
            all_history.extend(
                processor.get_detection_history(start_time, end_time)
            )
            
        # 按时间排序
        all_history.sort(key=lambda x: x['timestamp'])
        return all_history
