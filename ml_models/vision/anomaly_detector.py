"""
异常行为检测模型
"""
import torch
import torch.nn as nn
import torchvision.transforms as T
import numpy as np
from typing import Dict, List, Tuple
from .base_model import BaseVisionModel
from .config import MODEL_CONFIG, ANOMALY_CLASSES, PREPROCESSING_CONFIG

class AnomalyDetector(BaseVisionModel):
    def __init__(self, config: Dict = None):
        """
        初始化异常行为检测模型
        
        Args:
            config: 模型配置，如果为None则使用默认配置
        """
        if config is None:
            config = MODEL_CONFIG
        super().__init__(config)
        
        # 使用预训练的ResNet50作为特征提取器
        self.backbone = torch.hub.load('pytorch/vision:v0.10.0', 
                                     'resnet50', 
                                     pretrained=True)
        
        # 修改最后的全连接层以适应我们的类别数
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, len(ANOMALY_CLASSES)),
            nn.Sigmoid()
        )
        
        # 定义图像预处理流程
        self.transform = T.Compose([
            T.ToPILImage(),
            T.Resize(self.config['input_size']),
            T.ToTensor(),
            T.Normalize(mean=PREPROCESSING_CONFIG['normalize_mean'],
                       std=PREPROCESSING_CONFIG['normalize_std'])
        ])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        模型前向传播
        
        Args:
            x: 输入张量 (B, C, H, W)
            
        Returns:
            输出张量 (B, num_classes)
        """
        return self.backbone(x)

    def preprocess(self, image: np.ndarray) -> torch.Tensor:
        """
        图像预处理
        
        Args:
            image: 输入图像 (H, W, C)
            
        Returns:
            预处理后的张量 (1, C, H, W)
        """
        x = self.transform(image)
        return x.unsqueeze(0)  # 添加batch维度

    def postprocess(self, output: torch.Tensor) -> Dict:
        """
        后处理输出结果
        
        Args:
            output: 模型输出张量 (1, num_classes)
            
        Returns:
            处理后的结果字典，包含检测到的异常行为及其置信度
        """
        # 将输出转换为numpy数组
        probs = output.cpu().numpy().squeeze()
        
        # 获取置信度大于阈值的预测
        detections = []
        for i, prob in enumerate(probs):
            if prob > self.config['confidence_threshold']:
                detections.append({
                    'class_name': ANOMALY_CLASSES[i],
                    'confidence': float(prob)
                })
        
        return {
            'detections': detections,
            'raw_probabilities': {ANOMALY_CLASSES[i]: float(prob) 
                                for i, prob in enumerate(probs)}
        }

    def train_step(self, batch: Tuple[torch.Tensor, torch.Tensor],
                  criterion: nn.Module,
                  optimizer: torch.optim.Optimizer) -> float:
        """
        训练步骤
        
        Args:
            batch: (图像, 标签)元组
            criterion: 损失函数
            optimizer: 优化器
            
        Returns:
            损失值
        """
        images, labels = batch
        images = images.to(self.device)
        labels = labels.to(self.device)
        
        # 前向传播
        outputs = self(images)
        loss = criterion(outputs, labels)
        
        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        return loss.item()
