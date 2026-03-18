"""
Streamlit Web UI
图形化用户界面
"""

import streamlit as st
import os
from pathlib import Path
from photo_dedup.hash import ImageHasher, similarity, hamming_distance
from photo_dedup.scanner import PhotoScanner
from photo_dedup.cleaner import DuplicateCleaner
import pandas as pd


# 页面配置
st.set_page_config(
    page_title="AI Photo Deduplicator",
    page_icon="🖼️",
    layout="wide"
)


def main():
    """主界面"""
    
    st.title("🖼️ AI Photo Deduplicator")
    st.markdown("基于感知哈希与深度学习的智能照片去重工具")
    
    # 侧边栏
    st.sidebar.title("⚙️ 设置")
    
    # 算法选择
    algorithm = st.sidebar.selectbox(
        "检测算法",
        ["pHash", "dHash", "aHash", "ResNet50"]
    )
    
    # 相似度阈值
    threshold = st.sidebar.slider(
        "相似度阈值",
        min_value=0.5,
        max_value=1.0,
        value=0.85,
        step=0.05
    )
    
    # 保留策略
    keep_strategy = st.sidebar.selectbox(
        "保留策略",
        ["original", "largest", "newest", "first"]
    )
    
    # 主功能选项卡
    tab1, tab2, tab3 = st.tabs(["📁 批量扫描", "🔬 图片比较", "📊 清理结果"])
    
    # ========== 批量扫描 ==========
    with tab1:
        st.header("批量扫描重复照片")
        
        folder_path = st.text_input("📂 输入文件夹路径", 
                                   placeholder="/path/to/photos")
        
        if st.button("🔍 开始扫描"):
            if not folder_path:
                st.error("请输入文件夹路径")
            elif not Path(folder_path).exists():
                st.error("文件夹不存在")
            else:
                with st.spinner("正在扫描..."):
                    try:
                        scanner = PhotoScanner()
                        hasher = ImageHasher()
                        
                        # 获取图片文件
                        image_files = scanner.get_image_files(folder_path, recursive=True)
                        st.info(f"找到 {len(image_files)} 张图片")
                        
                        # 哈希分组
                        hash_groups = {}
                        progress_bar = st.progress(0)
                        
                        for i, img_path in enumerate(image_files):
                            try:
                                img_hash = hasher.phash(img_path)
                                if img_hash not in hash_groups:
                                    hash_groups[img_hash] = []
                                hash_groups[img_hash].append(str(img_path))
                            except Exception as e:
                                pass
                            
                            progress_bar.progress((i + 1) / len(image_files))
                        
                        # 筛选重复
                        duplicates = {k: v for k, v in hash_groups.items() if len(v) > 1}
                        
                        st.success(f"发现 {len(duplicates)} 组重复照片!")
                        
                        # 显示结果
                        for group_hash, files in duplicates.items():
                            with st.expander(f"📁 重复组 ({len(files)} 张)"):
                                for f in files:
                                    st.text(f)
                                    
                    except Exception as e:
                        st.error(f"扫描失败: {str(e)}")
    
    # ========== 图片比较 ==========
    with tab2:
        st.header("比较两张图片")
        
        col1, col2 = st.columns(2)
        
        with col1:
            img1_path = st.text_input("第一张图片路径", key="img1")
            
        with col2:
            img2_path = st.text_input("第二张图片路径", key="img2")
        
        if st.button("🔬 比较"):
            if not img1_path or not img2_path:
                st.error("请输入两张图片的路径")
            elif not Path(img1_path).exists() or not Path(img2_path).exists():
                st.error("图片文件不存在")
            else:
                try:
                    hasher = ImageHasher()
                    h1 = hasher.phash(img1_path)
                    h2 = hasher.phash(img2_path)
                    
                    dist = hamming_distance(h1, h2)
                    sim = similarity(h1, h2)
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("pHash 1", h1[:16] + "...")
                    col2.metric("pHash 2", h2[:16] + "...")
                    col3.metric("相似度", f"{sim:.1%}")
                    
                    st.progress(sim)
                    
                    if sim >= threshold:
                        st.success("✅ 两张图片相似!")
                    else:
                        st.info("❌ 两张图片不相似")
                        
                except Exception as e:
                    st.error(f"比较失败: {str(e)}")
    
    # ========== 清理结果 ==========
    with tab3:
        st.header("清理重复照片")
        
        st.info("请先在『批量扫描』选项卡中扫描重复照片，然后执行清理。")
        
        dry_run = st.checkbox("模拟运行（不实际删除）", value=True)
        
        if st.button("🧹 开始清理"):
            st.warning("清理功能需要先有扫描结果。当前为演示模式。")


if __name__ == "__main__":
    main()
