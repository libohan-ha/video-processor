"""
数据预处理和增强工具
"""
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
import albumentations as A
from typing import Dict, List, Tuple, Optional
from .config import PREPROCESSING_CONFIG

class ChargingDataset(Dataset):
    def __init__(self, 
                 image_paths: List[str],
                 labels: Optional[List[List[int]]] = None,
                 transform: Optional[A.Compose] = None,
                 is_training: bool = True):
        """
        充电场景数据集
        
        Args:
            image_paths: 图像路径列表
            labels: 标签列表（如果有）
            transform: albumentations数据增强转换
            is_training: 是否为训练模式
        """
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform
        self.is_training = is_training

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        # 读取图像
        image = cv2.imread(self.image_paths[idx])
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 应用数据增强
        if self.transform:
            if self.labels is not None:
                augmented = self.transform(image=image, 
                                        labels=self.labels[idx])
                image = augmented['image']
                label = torch.tensor(augmented['labels'], dtype=torch.float32)
            else:
                augmented = self.transform(image=image)
                image = augmented['image']
                label = None

        # 转换为tensor
        image = torch.from_numpy(image.transpose(2, 0, 1)).float()
        
        if self.labels is not None:
            return image, label
        return image

def get_train_transforms(input_size: Tuple[int, int]) -> A.Compose:
    """
    获取训练数据增强转换
    
    Args:
        input_size: 输入图像大小 (height, width)
        
    Returns:
        albumentations转换组合
    """
    return A.Compose([
        A.RandomResizedCrop(height=input_size[0], 
                           width=input_size[1],
                           scale=(0.8, 1.0)),
        A.HorizontalFlip(p=0.5),
        A.RandomBrightnessContrast(p=0.2),
        A.GaussNoise(p=0.2),
        A.Normalize(mean=PREPROCESSING_CONFIG['normalize_mean'],
                   std=PREPROCESSING_CONFIG['normalize_std']),
    ])

def get_val_transforms(input_size: Tuple[int, int]) -> A.Compose:
    """
    获取验证数据转换
    
    Args:
        input_size: 输入图像大小 (height, width)
        
    Returns:
        albumentations转换组合
    """
    return A.Compose([
        A.Resize(height=input_size[0], width=input_size[1]),
        A.Normalize(mean=PREPROCESSING_CONFIG['normalize_mean'],
                   std=PREPROCESSING_CONFIG['normalize_std']),
    ])

def prepare_batch(batch: List[torch.Tensor],
                 device: torch.device) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
    """
    准备批次数据
    
    Args:
        batch: 数据批次
        device: 设备
        
    Returns:
        处理后的图像和标签（如果有）
    """
    if isinstance(batch[0], tuple):
        images, labels = zip(*batch)
        images = torch.stack(images).to(device)
        labels = torch.stack(labels).to(device)
        return images, labels
    else:
        images = torch.stack(batch).to(device)
        return images, None
