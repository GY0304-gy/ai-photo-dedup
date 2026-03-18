"""
AI Photo Deduplicator - Main CLI Entry Point
命令行主入口
"""

import argparse
import sys
from pathlib import Path

from photo_dedup.hash import ImageHasher
from photo_dedup.similarity import SimilarityDetector
from photo_dedup.scanner import PhotoScanner
from photo_dedup.cleaner import DuplicateCleaner
import yaml


def load_config(config_path: str = None) -> dict:
    """加载配置文件"""
    if config_path is None:
        config_path = Path(__file__).parent / 'config.yaml'
    
    if Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    # 默认配置
    return {
        'similarity': {
            'threshold': 0.85,
            'algorithm': 'phash'
        },
        'processing': {
            'workers': 4,
            'batch_size': 32
        },
        'output': {
            'keep_strategy': 'original',
            'move_to_folder': './duplicates'
        }
    }


def cmd_scan(args):
    """扫描命令"""
    print(f"🔍 扫描文件夹: {args.folder}")
    
    scanner = PhotoScanner()
    
    # 获取图片文件
    image_files = scanner.get_image_files(args.folder, recursive=True)
    print(f"📷 找到 {len(image_files)} 张图片")
    
    # 根据算法分组
    if args.method == 'hash':
        # 使用哈希算法
        hasher = ImageHasher(hash_size=8)
        hash_groups = {}
        
        for img_path in image_files:
            try:
                img_hash = hasher.phash(img_path)
                if img_hash not in hash_groups:
                    hash_groups[img_hash] = []
                hash_groups[img_hash].append(str(img_path))
            except Exception as e:
                print(f"⚠️  处理失败: {img_path} - {e}")
        
        # 筛选重复的
        duplicates = {k: v for k, v in hash_groups.items() if len(v) > 1}
        
    elif args.method == 'ml':
        # 使用深度学习方法
        print("🤖 使用深度学习相似度检测...")
        detector = SimilarityDetector(model_name='resnet50')
        
        # 简化：只比较前100张（完整比较太慢）
        sample_files = image_files[:100]
        
        duplicates = []
        for i, img1 in enumerate(sample_files):
            for img2 in sample_files[i+1:]:
                try:
                    sim = detector.compare_images(img1, img2)
                    if sim >= args.threshold:
                        duplicates.append((img1, img2, sim))
                except Exception:
                    pass
        
        print(f"🔎 发现 {len(duplicates)} 对相似图片")
        return
    
    else:
        print(f"❌ 未知方法: {args.method}")
        return
    
    print(f"\n✅ 扫描完成!")
    print(f"📊 发现 {len(duplicates)} 组重复照片")
    
    # 输出结果
    for group_hash, files in duplicates.items():
        print(f"\n📁 重复组 ({len(files)} 张):")
        for f in files:
            print(f"   - {f}")


def cmd_clean(args):
    """清理命令"""
    print(f"🧹 清理文件夹: {args.folder}")
    
    # 先扫描
    scanner = PhotoScanner()
    hasher = ImageHasher(hash_size=8)
    
    image_files = scanner.get_image_files(args.folder, recursive=True)
    
    hash_groups = {}
    for img_path in image_files:
        try:
            img_hash = hasher.phash(img_path)
            if img_hash not in hash_groups:
                hash_groups[img_hash] = []
            hash_groups[img_hash].append(str(img_path))
        except Exception:
            pass
    
    duplicates = {k: v for k, v in hash_groups.items() if len(v) > 1}
    
    # 执行清理
    cleaner = DuplicateCleaner(keep_strategy=args.keep)
    
    output_folder = args.output if args.output else None
    
    results = cleaner.clean(
        duplicates, 
        output_folder=output_folder,
        dry_run=args.dry_run
    )
    
    # 输出报告
    report = cleaner.generate_report(results)
    print(report)


def cmd_compare(args):
    """比较命令"""
    print(f"🔬 比较两张图片: {args.image1} vs {args.image2}")
    
    if args.method == 'hash':
        hasher = ImageHasher()
        h1 = hasher.phash(args.image1)
        h2 = hasher.phash(args.image2)
        
        from photo_dedup.hash import hamming_distance, similarity
        dist = hamming_distance(h1, h2)
        sim = similarity(h1, h2)
        
        print(f"\n📊 哈希算法结果:")
        print(f"   pHash 1: {h1}")
        print(f"   pHash 2: {h2}")
        print(f"   汉明距离: {dist}")
        print(f"   相似度: {sim:.2%}")
        
    elif args.method == 'ml':
        detector = SimilarityDetector()
        sim = detector.compare_images(args.image1, args.image2)
        
        print(f"\n🤖 深度学习结果:")
        print(f"   相似度: {sim:.2%}")
    
    else:
        print(f"❌ 未知方法: {args.method}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='AI Photo Deduplicator - 智能照片去重工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # scan 命令
    scan_parser = subparsers.add_parser('scan', help='扫描重复照片')
    scan_parser.add_argument('folder', help='要扫描的文件夹')
    scan_parser.add_argument('--method', choices=['hash', 'ml'], default='hash',
                            help='检测方法 (hash=哈希算法, ml=深度学习)')
    scan_parser.add_argument('--threshold', type=float, default=0.85,
                            help='相似度阈值')
    
    # clean 命令
    clean_parser = subparsers.add_parser('clean', help='清理重复照片')
    clean_parser.add_argument('folder', help='要清理的文件夹')
    clean_parser.add_argument('--keep', choices=['original', 'largest', 'newest', 'first'],
                             default='original', help='保留策略')
    clean_parser.add_argument('--output', help='删除文件的移动目标文件夹')
    clean_parser.add_argument('--dry-run', action='store_true', 
                             help='模拟运行，不实际删除')
    
    # compare 命令
    compare_parser = subparsers.add_parser('compare', help='比较两张图片')
    compare_parser.add_argument('image1', help='第一张图片')
    compare_parser.add_argument('image2', help='第二张图片')
    compare_parser.add_argument('--method', choices=['hash', 'ml'], default='hash',
                               help='比较方法')
    
    args = parser.parse_args()
    
    if args.command == 'scan':
        cmd_scan(args)
    elif args.command == 'clean':
        cmd_clean(args)
    elif args.command == 'compare':
        cmd_compare(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
