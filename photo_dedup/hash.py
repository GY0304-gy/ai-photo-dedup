"""
Image Hashing Algorithms
实现多种感知哈希算法：pHash, dHash, aHash
"""

import cv2
import numpy as np
from PIL import Image
import imagehash
from typing import Union
from pathlib import Path


class ImageHasher:
    """图像哈希处理器"""
    
    def __init__(self, hash_size: int = 8):
        """
        初始化哈希处理器
        
        Args:
            hash_size: 哈希矩阵大小，默认 8x8
        """
        self.hash_size = hash_size
    
    def phash(self, image_path: Union[str, Path]) -> str:
        """
        感知哈希 (Perceptual Hash)
        基于 DCT 变换，感知更鲁棒
        
        Args:
            image_path: 图片路径
            
        Returns:
            16进制哈希字符串
        """
        img = Image.open(image_path)
        hash_obj = imagehash.phash(img, hash_size=self.hash_size)
        return str(hash_obj)
    
    def dhash(self, image_path: Union[str, Path]) -> str:
        """
        差异哈希 (Difference Hash)
        基于像素梯度变化，计算速度快
        
        Args:
            image_path: 图片路径
            
        Returns:
            16进制哈希字符串
        """
        img = Image.open(image_path)
        hash_obj = imagehash.dhash(img, hash_size=self.hash_size)
        return str(hash_obj)
    
    def ahash(self, image_path: Union[str, Path]) -> str:
        """
        平均哈希 (Average Hash)
        基于像素平均值，简单快速
        
        Args:
            image_path: 图片路径
            
        Returns:
            16进制哈希字符串
        """
        img = Image.open(image_path)
        hash_obj = imagehash.ahash(img, hash_size=self.hash_size)
        return str(hash_obj)
    
    def whash(self, image_path: Union[str, Path]) -> str:
        """
        小波哈希 (Wavelet Hash)
        基于小波变换，保留更多细节
        
        Args:
            image_path: 图片路径
            
        Returns:
            16进制哈希字符串
        """
        img = Image.open(image_path)
        hash_obj = imagehash.whash(img, hash_size=self.hash_size)
        return str(hash_obj)
    
    def get_all_hashes(self, image_path: Union[str, Path]) -> dict:
        """
        获取所有类型的哈希值
        
        Args:
            image_path: 图片路径
            
        Returns:
            包含所有哈希值的字典
        """
        return {
            'phash': self.phash(image_path),
            'dhash': self.dhash(image_path),
            'ahash': self.ahash(image_path),
            'whash': self.whash(image_path)
        }


def hamming_distance(hash1: str, hash2: str) -> int:
    """
    计算两个哈希值的汉明距离
    
    Args:
        hash1: 第一个哈希值 (16进制字符串)
        hash2: 第二个哈希值 (16进制字符串)
        
    Returns:
        汉明距离（不同位的数量）
    """
    if len(hash1) != len(hash2):
        # 长度不同，先对齐
        max_len = max(len(hash1), len(hash2))
        hash1 = hash1.zfill(max_len)
        hash2 = hash2.zfill(max_len)
    
    # 转换为二进制比较
    h1 = int(hash1, 16)
    h2 = int(hash2, 16)
    
    xor = h1 ^ h2
    distance = bin(xor).count('1')
    
    return distance


def similarity(hash1: str, hash2: str) -> float:
    """
    计算两个哈希值的相似度 (0-1)
    
    Args:
        hash1: 第一个哈希值
        hash2: 第二个哈希值
        
    Returns:
        相似度 (1.0 = 完全相同, 0.0 = 完全不同)
    """
    distance = hamming_distance(hash1, hash2)
    max_distance = len(hash1) * 4  # 16进制每字符4位
    
    return 1.0 - (distance / max_distance)


if __name__ == "__main__":
    # 测试代码
    hasher = ImageHasher()
    
    # 示例用法
    print("Image Hasher Test")
    print("=" * 30)
    print(f"Hash size: {hasher.hash_size}x{hasher.hash_size}")
    print("Methods available: phash, dhash, ahash, whash")
