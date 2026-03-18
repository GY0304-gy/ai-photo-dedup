"""
Duplicate Photo Cleaner
重复照片清理逻辑
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from PIL import Image
import json


class DuplicateCleaner:
    """重复照片清理器"""
    
    def __init__(self, keep_strategy: str = 'original'):
        """
        初始化清理器
        
        Args:
            keep_strategy: 保留策略
                - 'original': 保留文件名包含 'original' 的
                - 'first': 保留第一个
                - 'largest': 保留分辨率最高的
                - 'newest': 保留修改时间最新的
        """
        self.keep_strategy = keep_strategy
    
    def decide_keep(self, file_list: List[str]) -> Tuple[str, List[str]]:
        """
        决定保留哪个文件，删除其他的
        
        Args:
            file_list: 重复文件列表
            
        Returns:
            (保留的文件路径, 要删除的文件列表)
        """
        if len(file_list) <= 1:
            return file_list[0] if file_list else '', []
        
        # 根据策略选择保留的文件
        if self.keep_strategy == 'original':
            keep_file = self._keep_original(file_list)
        elif self.keep_strategy == 'largest':
            keep_file = self._keep_largest(file_list)
        elif self.keep_strategy == 'newest':
            keep_file = self._keep_newest(file_list)
        else:  # 'first'
            keep_file = file_list[0]
        
        # 要删除的列表
        delete_files = [f for f in file_list if f != keep_file]
        
        return keep_file, delete_files
    
    def _keep_original(self, file_list: List[str]) -> str:
        """保留文件名包含 'original' 的"""
        for f in file_list:
            if 'original' in Path(f).stem.lower():
                return f
        # 如果没有 original，返回第一个
        return file_list[0]
    
    def _keep_largest(self, file_list: List[str]) -> str:
        """保留分辨率（面积）最大的"""
        max_area = 0
        keep_file = file_list[0]
        
        for f in file_list:
            try:
                with Image.open(f) as img:
                    area = img.width * img.height
                    if area > max_area:
                        max_area = area
                        keep_file = f
            except Exception:
                continue
        
        return keep_file
    
    def _keep_newest(self, file_list: List[str]) -> str:
        """保留修改时间最新的"""
        max_mtime = 0
        keep_file = file_list[0]
        
        for f in file_list:
            try:
                mtime = Path(f).stat().st_mtime
                if mtime > max_mtime:
                    max_mtime = mtime
                    keep_file = f
            except Exception:
                continue
        
        return keep_file
    
    def clean(self, duplicate_groups: Dict[str, List[str]], 
              output_folder: Optional[str] = None,
              dry_run: bool = True) -> Dict:
        """
        执行清理操作
        
        Args:
            duplicate_groups: 重复文件分组 {hash: [files]}
            output_folder: 删除文件的移动目标文件夹（可选）
            dry_run: 模拟运行，不实际删除
            
        Returns:
            清理结果统计
        """
        results = {
            'total_groups': len(duplicate_groups),
            'files_kept': [],
            'files_deleted': [],
            'space_saved': 0,
            'errors': []
        }
        
        for group_hash, file_list in duplicate_groups.items():
            keep_file, delete_files = self.decide_keep(file_list)
            
            results['files_kept'].append(keep_file)
            
            for del_file in delete_files:
                try:
                    file_size = Path(del_file).stat().st_size
                    
                    if output_folder and not dry_run:
                        # 移动到目标文件夹
                        dest_folder = Path(output_folder)
                        dest_folder.mkdir(parents=True, exist_ok=True)
                        
                        dest_path = dest_folder / Path(del_file).name
                        shutil.move(del_file, dest_path)
                    elif not dry_run:
                        # 直接删除
                        os.remove(del_file)
                    
                    results['files_deleted'].append(del_file)
                    results['space_saved'] += file_size
                    
                except Exception as e:
                    results['errors'].append({
                        'file': del_file,
                        'error': str(e)
                    })
        
        # 转换空间节省为 MB
        results['space_saved_mb'] = results['space_saved'] / (1024 * 1024)
        
        return results
    
    def generate_report(self, results: Dict, output_path: str = None) -> str:
        """
        生成清理报告
        
        Args:
            results: 清理结果
            output_path: 报告输出路径（可选）
            
        Returns:
            报告内容
        """
        report_lines = [
            "=" * 50,
            "AI Photo Deduplicator - 清理报告",
            "=" * 50,
            "",
            f"📊 总重复组数: {results['total_groups']}",
            f"✅ 保留文件数: {len(results['files_kept'])}",
            f"🗑️  删除文件数: {len(results['files_deleted'])}",
            f"💾 节省空间: {results['space_saved_mb']:.2f} MB",
            "",
            "-" * 50,
            "保留的文件:",
            "-" * 50,
        ]
        
        for f in results['files_kept']:
            report_lines.append(f"  ✅ {f}")
        
        report_lines.extend([
            "",
            "-" * 50,
            "删除的文件:",
            "-" * 50,
        ])
        
        for f in results['files_deleted']:
            report_lines.append(f"  ❌ {f}")
        
        if results['errors']:
            report_lines.extend([
                "",
                "-" * 50,
                "错误:",
                "-" * 50,
            ])
            for err in results['errors']:
                report_lines.append(f"  ⚠️  {err['file']}: {err['error']}")
        
        report_lines.append("")
        report_lines.append("=" * 50)
        
        report_content = "\n".join(report_lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
        
        return report_content


def clean_duplicates(duplicate_groups: Dict[str, List[str]], 
                     keep_strategy: str = 'original',
                     output_folder: str = None,
                     dry_run: bool = True) -> Dict:
    """
    便捷函数：快速执行清理
    
    Args:
        duplicate_groups: 重复文件分组
        keep_strategy: 保留策略
        output_folder: 删除文件移动目标
        dry_run: 是否模拟运行
        
    Returns:
        清理结果
    """
    cleaner = DuplicateCleaner(keep_strategy=keep_strategy)
    return cleaner.clean(duplicate_groups, output_folder, dry_run)


if __name__ == "__main__":
    # 测试代码
    print("Duplicate Cleaner Test")
    print("=" * 30)
    print("Strategies: original, largest, newest, first")
    print("\nUsage:")
    print("  cleaner = DuplicateCleaner(keep_strategy='original')")
    print("  results = cleaner.clean(duplicate_groups)")
