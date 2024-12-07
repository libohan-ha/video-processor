"""
火灾隐患检测模型
"""
import torch
import torch.nn as nn
import torchvision.models as models
import numpy as np
from typing import Dict, List, Tuple
from .base_model import BaseVisionModel
from .config import MODEL_CONFIG, FIRE_HAZARD_CLASSES, PREPROCESSING_CONFIG

class FireHazardDetector(BaseVisionModel):
    def __init__(self, config: Dict = None):
        """
        初始化火灾隐患检测模型
        
        Args:
            config: 模型配置，如果为None则使用默认配置
        """
        if config is None:
            config = MODEL_CONFIG
        super().__init__(config)
        
        # 使用EfficientNet-B4作为基础模型
        self.backbone = models.efficientnet_b4(pretrained=True)
        
        # 修改最后的分类层
        num_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.4, inplace=True),
            nn.Linear(num_features, len(FIRE_HAZARD_CLASSES)),
            nn.Sigmoid()
        )
        
        # 添加热力图生成层
        self.gradcam_hooks = []
        self.gradient = None
        self.activation = None
        
        def backward_hook(module, grad_input, grad_output):
            self.gradient = grad_output[0]
            
        def forward_hook(module, input, output):
            self.activation = output
            
        # 注册hooks用于GradCAM
        target_layer = self.backbone.features[-1]
        self.gradcam_hooks.append(target_layer.register_forward_hook(forward_hook))
        self.gradcam_hooks.append(target_layer.register_backward_hook(backward_hook))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        模型前向传播
        
        Args:
            x: 输入张量 (B, C, H, W)
            
        Returns:
            输出张量 (B, num_classes)
        """
        return self.backbone(x)

    def generate_heatmap(self, 
                        image: torch.Tensor,
                        target_class: int) -> np.ndarray:
        """
        生成类激活热力图
        
        Args:
            image: 输入图像张量
            target_class: 目标类别索引
            
        Returns:
            热力图数组
        """
        # 前向传播
        output = self(image)
        
        # 清除之前的梯度
        self.zero_grad()
        
        # 计算目标类别的梯度
        target = torch.zeros_like(output)
        target[0, target_class] = 1
        output.backward(gradient=target)
        
        # 生成热力图
        weights = torch.mean(self.gradient, dim=(2, 3))[0]
        activation = self.activation[0]
        
        cam = torch.zeros(activation.shape[1:], dtype=torch.float32)
        for i, w in enumerate(weights):
            cam += w * activation[i]
            
        cam = torch.relu(cam)
        cam = cam.detach().cpu().numpy()
        
        # 归一化
        cam = cv2.resize(cam, (image.shape[3], image.shape[2]))
        cam = (cam - cam.min()) / (cam.max() - cam.min())
        
        return cam

    def preprocess(self, image: np.ndarray) -> torch.Tensor:
        """
        图像预处理
        
        Args:
            image: 输入图像 (H, W, C)
            
        Returns:
            预处理后的张量 (1, C, H, W)
        """
        # 调整图像大小
        image = cv2.resize(image, self.config['input_size'])
        
        # 归一化
        image = image.astype(np.float32) / 255.0
        image = (image - np.array(PREPROCESSING_CONFIG['normalize_mean'])) / \
                np.array(PREPROCESSING_CONFIG['normalize_std'])
        
        # 转换为tensor
        image = torch.from_numpy(image.transpose(2, 0, 1)).float()
        return image.unsqueeze(0)

    def postprocess(self, output: torch.Tensor) -> Dict:
        """
        后处理输出结果
        
        Args:
            output: 模型输出张量 (1, num_classes)
            
        Returns:
            处理后的结果字典
        """
        # 将输出转换为numpy数组
        probs = output.cpu().numpy().squeeze()
        
        # 获取置信度大于阈值的预测
        detections = []
        for i, prob in enumerate(probs):
            if prob > self.config['confidence_threshold']:
                detections.append({
                    'class_name': FIRE_HAZARD_CLASSES[i],
                    'confidence': float(prob)
                })
                
                # 如果检测到危险情况，生成热力图
                if i > 0:  # 非正常类别
                    heatmap = self.generate_heatmap(
                        output.to(self.device),
                        i
                    )
                    detections[-1]['heatmap'] = heatmap.tolist()
        
        return {
            'detections': detections,
            'raw_probabilities': {FIRE_HAZARD_CLASSES[i]: float(prob) 
                                for i, prob in enumerate(probs)}
        }

    def __del__(self):
        """
        清理hooks
        """
        for hook in self.gradcam_hooks:
            hook.remove()
