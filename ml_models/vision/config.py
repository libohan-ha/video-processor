"""
视觉识别模块配置文件
"""

# 模型配置
MODEL_CONFIG = {
    'input_size': (640, 640),  # 输入图像尺寸
    'confidence_threshold': 0.5,  # 检测置信度阈值
    'iou_threshold': 0.45,  # NMS IOU阈值
}

# 异常行为类别
ANOMALY_CLASSES = {
    0: 'normal',  # 正常行为
    1: 'smoking',  # 吸烟
    2: 'unauthorized_charging',  # 未授权充电
    3: 'cable_damage',  # 充电线损坏
    4: 'improper_parking',  # 停车不当
}

# 火灾隐患类别
FIRE_HAZARD_CLASSES = {
    0: 'normal',  # 正常
    1: 'smoke',  # 烟雾
    2: 'spark',  # 火花
    3: 'overheat',  # 过热
}

# 设备状态类别
EQUIPMENT_STATUS_CLASSES = {
    0: 'normal',  # 正常
    1: 'damaged',  # 设备损坏
    2: 'unauthorized_access',  # 未授权访问
    3: 'tampered',  # 设备被篡改
}

# 图像预处理配置
PREPROCESSING_CONFIG = {
    'normalize_mean': [0.485, 0.456, 0.406],  # 归一化均值
    'normalize_std': [0.229, 0.224, 0.225],  # 归一化标准差
    'use_augmentation': True,  # 是否使用数据增强
}

# 训练配置
TRAINING_CONFIG = {
    'batch_size': 16,
    'num_epochs': 100,
    'learning_rate': 0.001,
    'weight_decay': 0.0005,
    'early_stopping_patience': 10,
}

# 设备配置
DEVICE_CONFIG = {
    'use_cuda': True,  # 是否使用GPU
    'gpu_id': 0,  # GPU ID
}
