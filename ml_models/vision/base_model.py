"""
视觉识别模型基类
"""
import torch
import torch.nn as nn
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Union
import numpy as np

class BaseVisionModel(ABC, nn.Module):
    def __init__(self, config: Dict):
        """
        初始化基础视觉模型
        
        Args:
            config: 模型配置字典
        """
        super().__init__()
        self.config = config
        self.device = torch.device(
            f"cuda:{config['gpu_id']}" if torch.cuda.is_available() and config['use_cuda']
            else "cpu"
        )

    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        模型前向传播
        
        Args:
            x: 输入张量
            
        Returns:
            输出张量
        """
        pass

    @abstractmethod
    def preprocess(self, image: np.ndarray) -> torch.Tensor:
        """
        图像预处理
        
        Args:
            image: 输入图像 (H, W, C)
            
        Returns:
            预处理后的张量
        """
        pass

    @abstractmethod
    def postprocess(self, output: torch.Tensor) -> Dict:
        """
        后处理输出结果
        
        Args:
            output: 模型输出张量
            
        Returns:
            处理后的结果字典
        """
        pass

    def predict(self, image: np.ndarray) -> Dict:
        """
        预测单张图像
        
        Args:
            image: 输入图像
            
        Returns:
            预测结果字典
        """
        # 预处理
        x = self.preprocess(image)
        x = x.to(self.device)

        # 推理
        with torch.no_grad():
            output = self.forward(x)

        # 后处理
        results = self.postprocess(output)
        return results

    def save_model(self, path: str):
        """
        保存模型
        
        Args:
            path: 模型保存路径
        """
        torch.save({
            'model_state_dict': self.state_dict(),
            'config': self.config
        }, path)

    def load_model(self, path: str):
        """
        加载模型
        
        Args:
            path: 模型加载路径
        """
        checkpoint = torch.load(path, map_location=self.device)
        self.load_state_dict(checkpoint['model_state_dict'])
        self.config.update(checkpoint['config'])
