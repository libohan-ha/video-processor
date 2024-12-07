"""
模型训练和评估
"""
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Dict, List, Optional, Tuple
import logging
import time
from pathlib import Path
import numpy as np
from sklearn.metrics import precision_recall_fscore_support

from .anomaly_detector import AnomalyDetector
from .data_utils import ChargingDataset, get_train_transforms, get_val_transforms, prepare_batch
from .config import MODEL_CONFIG, TRAINING_CONFIG

class ModelTrainer:
    def __init__(self,
                 model: nn.Module,
                 train_loader: DataLoader,
                 val_loader: Optional[DataLoader] = None,
                 config: Dict = None):
        """
        模型训练器
        
        Args:
            model: 待训练的模型
            train_loader: 训练数据加载器
            val_loader: 验证数据加载器（可选）
            config: 训练配置
        """
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.config = config or TRAINING_CONFIG
        
        # 设置设备
        self.device = next(model.parameters()).device
        
        # 设置损失函数和优化器
        self.criterion = nn.BCELoss()
        self.optimizer = torch.optim.Adam(
            model.parameters(),
            lr=self.config['learning_rate'],
            weight_decay=self.config['weight_decay']
        )
        
        # 设置学习率调度器
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.1,
            patience=5,
            verbose=True
        )
        
        # 初始化最佳模型状态
        self.best_val_loss = float('inf')
        self.best_model_state = None
        self.patience_counter = 0
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def train_epoch(self) -> float:
        """
        训练一个epoch
        
        Returns:
            平均训练损失
        """
        self.model.train()
        total_loss = 0
        num_batches = len(self.train_loader)
        
        for batch_idx, (images, labels) in enumerate(self.train_loader):
            images, labels = prepare_batch((images, labels), self.device)
            
            # 前向传播
            outputs = self.model(images)
            loss = self.criterion(outputs, labels)
            
            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            
            if (batch_idx + 1) % 10 == 0:
                self.logger.info(f'Batch [{batch_idx + 1}/{num_batches}], '
                               f'Loss: {loss.item():.4f}')
        
        return total_loss / num_batches

    def validate(self) -> Tuple[float, Dict[str, float]]:
        """
        验证模型
        
        Returns:
            验证损失和评估指标
        """
        if not self.val_loader:
            return 0.0, {}
        
        self.model.eval()
        total_loss = 0
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for images, labels in self.val_loader:
                images, labels = prepare_batch((images, labels), self.device)
                outputs = self.model(images)
                loss = self.criterion(outputs, labels)
                total_loss += loss.item()
                
                # 收集预测和标签
                preds = (outputs > 0.5).float().cpu().numpy()
                labels = labels.cpu().numpy()
                all_preds.extend(preds)
                all_labels.extend(labels)
        
        # 计算评估指标
        precision, recall, f1, _ = precision_recall_fscore_support(
            np.array(all_labels),
            np.array(all_preds),
            average='weighted'
        )
        
        metrics = {
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
        
        return total_loss / len(self.val_loader), metrics

    def train(self, num_epochs: int, save_dir: str):
        """
        训练模型
        
        Args:
            num_epochs: 训练轮数
            save_dir: 模型保存目录
        """
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        for epoch in range(num_epochs):
            start_time = time.time()
            
            # 训练一个epoch
            train_loss = self.train_epoch()
            
            # 验证
            val_loss, metrics = self.validate()
            
            # 更新学习率
            if self.val_loader:
                self.scheduler.step(val_loss)
            
            # 保存最佳模型
            if self.val_loader and val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.best_model_state = self.model.state_dict()
                self.patience_counter = 0
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': self.best_model_state,
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'val_loss': val_loss,
                    'metrics': metrics
                }, save_dir / 'best_model.pth')
            else:
                self.patience_counter += 1
            
            # 早停
            if self.patience_counter >= self.config['early_stopping_patience']:
                self.logger.info('Early stopping triggered')
                break
            
            # 记录训练信息
            epoch_time = time.time() - start_time
            self.logger.info(
                f'Epoch [{epoch+1}/{num_epochs}], '
                f'Train Loss: {train_loss:.4f}, '
                f'Val Loss: {val_loss:.4f}, '
                f'Metrics: {metrics}, '
                f'Time: {epoch_time:.2f}s'
            )
        
        # 训练结束，加载最佳模型
        if self.best_model_state is not None:
            self.model.load_state_dict(self.best_model_state)
            self.logger.info(f'Training completed. Best val loss: {self.best_val_loss:.4f}')
