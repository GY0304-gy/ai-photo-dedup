"""
Deep Learning Similarity Detection
基于深度学习的图像相似度检测 (ResNet/VGG)
"""

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np
from typing import Union, List, Tuple
from pathlib import Path
import warnings


class SimilarityDetector:
    """深度学习相似度检测器"""
    
    def __init__(self, model_name: str = 'resnet50', device: str = None):
        """
        初始化相似度检测器
        
        Args:
            model_name: 模型名称 (resnet50, vgg16, efficientnet_b0)
            device: 计算设备 (cuda/cpu)，默认自动选择
        """
        self.model_name = model_name
        
        # 自动选择设备
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        # 加载预训练模型
        self.model = self._load_model()
        self.model.eval()
        
        # 图像预处理
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    
    def _load_model(self) -> nn.Module:
        """加载预训练模型"""
        if self.model_name == 'resnet50':
            model = models.resnet50(pretrained=True)
            # 移除最后的分类层
            model = nn.Sequential(*list(model.children())[:-1])
        elif self.model_name == 'resnet18':
            model = models.resnet18(pretrained=True)
            model = nn.Sequential(*list(model.children())[:-1])
        elif self.model_name == 'vgg16':
            model = models.vgg16(pretrained=True)
            model = nn.Sequential(*list(model.features.children()),
                                  nn.AdaptiveAvgPool2d(1),
                                  nn.Flatten())
        elif self.model_name == 'efficientnet_b0':
            model = models.efficientnet_b0(pretrained=True)
            model = nn.Sequential(*list(model.children())[:-1])
        else:
            warnings.warn(f"Unknown model {self.model_name}, using resnet50")
            model = models.resnet50(pretrained=True)
            model = nn.Sequential(*list(model.children())[:-1])
        
        return model.to(self.device)
    
    def extract_features(self, image_path: Union[str, Path]) -> np.ndarray:
        """
        提取图像特征向量
        
        Args:
            image_path: 图像路径
            
        Returns:
            特征向量 (numpy array)
        """
        img = Image.open(image_path).convert('RGB')
        img_tensor = self.transform(img).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            features = self.model(img_tensor)
        
        return features.cpu().numpy().flatten()
    
    def cosine_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """
        计算余弦相似度
        
        Args:
            features1: 第一个特征向量
            features2: 第二个特征向量
            
        Returns:
            相似度 (-1 到 1)
        """
        dot_product = np.dot(features1, features2)
        norm1 = np.linalg.norm(features1)
        norm2 = np.linalg.norm(features2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def euclidean_distance(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """
        计算欧氏距离
        
        Args:
            features1: 第一个特征向量
            features2: 第二个特征向量
            
        Returns:
            欧氏距离
        """
        return np.linalg.norm(features1 - features2)
    
    def compare_images(self, image1: Union[str, Path], 
                       image2: Union[str, Path],
                       method: str = 'cosine') -> float:
        """
        比较两张图片的相似度
        
        Args:
            image1: 第一张图片路径
            image2: 第二张图片路径
            method: 相似度计算方法 (cosine/euclidean)
            
        Returns:
            相似度分数
        """
        features1 = self.extract_features(image1)
        features2 = self.extract_features(image2)
        
        if method == 'cosine':
            similarity = self.cosine_similarity(features1, features2)
            # 转换到 0-1 范围
            return (similarity + 1) / 2
        elif method == 'euclidean':
            distance = self.euclidean_distance(features1, features2)
            # 转换到 0-1 范围（距离越小越相似）
            return 1.0 / (1.0 + distance)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def find_similar(self, target_image: Union[str, Path],
                     image_folder: Union[str, Path],
                     threshold: float = 0.85,
                     top_k: int = 10) -> List[Tuple[str, float]]:
        """
        在文件夹中查找与目标图片相似的图片
        
        Args:
            target_image: 目标图片路径
            image_folder: 图片文件夹路径
            threshold: 相似度阈值
            top_k: 返回前 k 个最相似的图片
            
        Returns:
            List of (图片路径, 相似度) 元组
        """
        target_features = self.extract_features(target_image)
        
        folder_path = Path(image_folder)
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'}
        
        results = []
        
        for img_path in folder_path.rglob('*'):
            if img_path.suffix.lower() in image_extensions:
                try:
                    features = self.extract_features(img_path)
                    sim = self.cosine_similarity(target_features, features)
                    sim_normalized = (sim + 1) / 2
                    
                    if sim_normalized >= threshold:
                        results.append((str(img_path), sim_normalized))
                except Exception as e:
                    warnings.warn(f"Failed to process {img_path}: {e}")
        
        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]


# 便捷函数
def compute_similarity(image1: str, image2: str, 
                       model: str = 'resnet50') -> float:
    """
    快速计算两张图片的相似度
    
    Args:
        image1: 图片1路径
        image2: 图片2路径
        model: 使用的模型
        
    Returns:
        相似度 (0-1)
    """
    detector = SimilarityDetector(model_name=model)
    return detector.compare_images(image1, image2)


if __name__ == "__main__":
    # 测试代码
    print("Deep Learning Similarity Detector Test")
    print("=" * 40)
    print("Model: ResNet50")
    print("Device: ", end="")
    detector = SimilarityDetector()
    print(detector.device)
    print("\nUsage:")
    print("  detector.compare_images('img1.jpg', 'img2.jpg')")
    print("  detector.find_similar('target.jpg', 'folder/')")
