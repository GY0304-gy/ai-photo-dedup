"""
File Scanner
文件夹扫描与图片查找
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import threading


class PhotoScanner:
    """照片扫描器"""
    
    def __init__(self, supported_formats: Optional[List[str]] = None):
        """
        初始化扫描器
        
        Args:
            supported_formats: 支持的图片格式列表
        """
        if supported_formats is None:
            self.supported_formats = {
                '.jpg', '.jpeg', '.png', '.bmp', 
                '.webp', '.tiff', '.tif', '.gif'
            }
        else:
            self.supported_formats = set(supported_formats)
        
        self._lock = threading.Lock()
    
    def is_image(self, file_path: Path) -> bool:
        """检查文件是否为图片"""
        return file_path.suffix.lower() in self.supported_formats
    
    def get_image_files(self, folder: str, recursive: bool = True) -> List[Path]:
        """
        获取文件夹中的所有图片文件
        
        Args:
            folder: 文件夹路径
            recursive: 是否递归扫描子文件夹
            
        Returns:
            图片文件路径列表
        """
        folder_path = Path(folder)
        
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder}")
        
        if not folder_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {folder}")
        
        image_files = []
        
        if recursive:
            for file_path in folder_path.rglob('*'):
                if file_path.is_file() and self.is_image(file_path):
                    image_files.append(file_path)
        else:
            for file_path in folder_path.iterdir():
                if file_path.is_file() and self.is_image(file_path):
                    image_files.append(file_path)
        
        return sorted(image_files)
    
    def compute_file_hash(self, file_path: Path, algorithm: str = 'md5') -> str:
        """
        计算文件的哈希值（用于快速查重）
        
        Args:
            file_path: 文件路径
            algorithm: 哈希算法 (md5/sha1/sha256)
            
        Returns:
            哈希值字符串
        """
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            # 读取文件前 64KB 用于快速比较
            chunk = f.read(65536)
            hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    def get_file_info(self, file_path: Path) -> Dict:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            包含文件信息的字典
        """
        stat = file_path.stat()
        
        return {
            'path': str(file_path),
            'name': file_path.name,
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'extension': file_path.suffix.lower()
        }
    
    def scan_with_thumbnail_hash(self, folder: str, 
                                  recursive: bool = True,
                                  workers: int = 4) -> Dict[str, List[str]]:
        """
        扫描文件夹，按文件哈希分组（快速查重）
        
        Args:
            folder: 文件夹路径
            recursive: 是否递归
            workers: 并行线程数
            
        Returns:
            {哈希值: [文件路径列表]}
        """
        image_files = self.get_image_files(folder, recursive)
        hash_groups = {}
        
        def process_file(file_path: Path):
            file_hash = self.compute_file_hash(file_path)
            return file_hash, str(file_path)
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_file, f): f for f in image_files}
            
            for future in tqdm(as_completed(futures), 
                             total=len(futures), 
                             desc="Scanning"):
                file_hash, file_path = future.result()
                
                if file_hash not in hash_groups:
                    hash_groups[file_hash] = []
                hash_groups[file_hash].append(file_path)
        
        # 只保留有多个文件的组（重复文件）
        duplicates = {k: v for k, v in hash_groups.items() if len(v) > 1}
        
        return duplicates
    
    def scan_with_size_check(self, folder: str,
                            recursive: bool = True) -> Dict[int, List[str]]:
        """
        按文件大小分组（初步筛选可能重复的文件）
        
        Args:
            folder: 文件夹路径
            recursive: 是否递归
            
        Returns:
            {文件大小: [文件路径列表]}
        """
        image_files = self.get_image_files(folder, recursive)
        size_groups = {}
        
        for file_path in image_files:
            size = file_path.stat().st_size
            
            if size not in size_groups:
                size_groups[size] = []
            size_groups[size].append(str(file_path))
        
        # 只保留大小相同的文件
        duplicates = {k: v for k, v in size_groups.items() if len(v) > 1}
        
        return duplicates
    
    def get_folder_stats(self, folder: str, recursive: bool = True) -> Dict:
        """
        获取文件夹统计信息
        
        Args:
            folder: 文件夹路径
            recursive: 是否递归
            
        Returns:
            统计信息字典
        """
        image_files = self.get_image_files(folder, recursive)
        
        total_size = sum(f.stat().st_size for f in image_files)
        
        extensions = {}
        for f in image_files:
            ext = f.suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1
        
        return {
            'total_files': len(image_files),
            'total_size': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'extensions': extensions
        }


if __name__ == "__main__":
    # 测试代码
    scanner = PhotoScanner()
    print("Photo Scanner Test")
    print("=" * 30)
    print(f"Supported formats: {scanner.supported_formats}")
    print("\nUsage:")
    print("  scanner.get_image_files('/path/to/folder')")
    print("  scanner.scan_with_thumbnail_hash('/path/to/folder')")
