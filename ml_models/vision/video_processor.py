"""
视频流处理模块
"""
import cv2
import numpy as np
import threading
import queue
import time
from typing import Dict, Optional, Tuple, List
import logging
from datetime import datetime

from .anomaly_detector import AnomalyDetector
from .config import MODEL_CONFIG

class VideoProcessor:
    def __init__(self, 
                 model: AnomalyDetector,
                 source: str = "0",  # 可以是摄像头索引或视频文件路径
                 buffer_size: int = 30,
                 detection_interval: float = 0.5):  # 检测间隔（秒）
        """
        视频流处理器
        
        Args:
            model: 异常检测模型
            source: 视频源（摄像头索引或视频文件路径）
            buffer_size: 帧缓冲区大小
            detection_interval: 检测间隔（秒）
        """
        self.model = model
        self.source = source
        self.buffer_size = buffer_size
        self.detection_interval = detection_interval
        
        # 初始化视频捕获
        self.cap = None
        self.frame_width = None
        self.frame_height = None
        self.fps = None
        
        # 初始化缓冲区和线程
        self.frame_buffer = queue.Queue(maxsize=buffer_size)
        self.result_buffer = queue.Queue(maxsize=buffer_size)
        self.is_running = False
        self.threads = []
        
        # 初始化日志
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # 初始化检测结果存储
        self.latest_detection = None
        self.detection_history = []

    def start(self):
        """
        启动视频处理
        """
        if self.is_running:
            return
        
        # 初始化视频捕获
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开视频源: {self.source}")
        
        # 获取视频属性
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        self.is_running = True
        
        # 启动工作线程
        self.threads = [
            threading.Thread(target=self._capture_thread, daemon=True),
            threading.Thread(target=self._detection_thread, daemon=True)
        ]
        
        for thread in self.threads:
            thread.start()
            
        self.logger.info("视频处理器已启动")

    def stop(self):
        """
        停止视频处理
        """
        self.is_running = False
        
        # 等待线程结束
        for thread in self.threads:
            thread.join()
            
        # 释放资源
        if self.cap is not None:
            self.cap.release()
            
        self.logger.info("视频处理器已停止")

    def _capture_thread(self):
        """
        视频捕获线程
        """
        while self.is_running:
            if self.cap is None:
                break
                
            ret, frame = self.cap.read()
            if not ret:
                break
                
            # 如果缓冲区满，移除最旧的帧
            if self.frame_buffer.full():
                try:
                    self.frame_buffer.get_nowait()
                except queue.Empty:
                    pass
                    
            try:
                self.frame_buffer.put_nowait(frame)
            except queue.Full:
                pass

    def _detection_thread(self):
        """
        异常检测线程
        """
        last_detection_time = 0
        
        while self.is_running:
            current_time = time.time()
            
            # 控制检测频率
            if current_time - last_detection_time < self.detection_interval:
                time.sleep(0.01)
                continue
                
            try:
                frame = self.frame_buffer.get_nowait()
            except queue.Empty:
                continue
                
            # 执行异常检测
            try:
                results = self.model.predict(frame)
                
                # 添加时间戳
                results['timestamp'] = datetime.now().isoformat()
                results['frame_info'] = {
                    'width': self.frame_width,
                    'height': self.frame_height
                }
                
                # 更新检测结果
                self.latest_detection = results
                self.detection_history.append(results)
                
                # 保持历史记录在合理范围内
                if len(self.detection_history) > 1000:
                    self.detection_history.pop(0)
                
                # 存储处理后的帧和结果
                if not self.result_buffer.full():
                    self.result_buffer.put_nowait((frame, results))
                    
                last_detection_time = current_time
                
            except Exception as e:
                self.logger.error(f"检测过程发生错误: {str(e)}")

    def get_latest_frame(self) -> Tuple[Optional[np.ndarray], Optional[Dict]]:
        """
        获取最新的处理后帧和检测结果
        
        Returns:
            帧和检测结果的元组
        """
        try:
            return self.result_buffer.get_nowait()
        except queue.Empty:
            return None, None

    def get_detection_history(self, 
                            start_time: Optional[str] = None,
                            end_time: Optional[str] = None) -> List[Dict]:
        """
        获取指定时间范围内的检测历史
        
        Args:
            start_time: 开始时间（ISO格式）
            end_time: 结束时间（ISO格式）
            
        Returns:
            检测结果列表
        """
        if start_time is None and end_time is None:
            return self.detection_history
            
        filtered_history = []
        for result in self.detection_history:
            result_time = datetime.fromisoformat(result['timestamp'])
            
            if start_time and result_time < datetime.fromisoformat(start_time):
                continue
            if end_time and result_time > datetime.fromisoformat(end_time):
                continue
                
            filtered_history.append(result)
            
        return filtered_history

    def draw_detection_results(self, 
                             frame: np.ndarray,
                             results: Dict) -> np.ndarray:
        """
        在帧上绘制检测结果
        
        Args:
            frame: 输入帧
            results: 检测结果
            
        Returns:
            绘制了检测结果的帧
        """
        frame = frame.copy()
        
        # 绘制检测到的异常
        if 'detections' in results:
            for detection in results['detections']:
                text = f"{detection['class_name']}: {detection['confidence']:.2f}"
                cv2.putText(frame, text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # 添加时间戳
        if 'timestamp' in results:
            timestamp = datetime.fromisoformat(results['timestamp'])
            time_text = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, time_text, (10, frame.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
