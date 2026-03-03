#!/usr/bin/env python3
"""
图片识别测试工具
用于测试和调试图片识别算法
"""
import os
import sys
import cv2
import numpy as np
import mss
from main import find_image_on_screen, ASSETS_DIR

def test_all_images():
    """测试所有图片的识别效果"""
    print("=" * 60)
    print("图片识别测试工具")
    print("=" * 60)
    
    if not os.path.exists(ASSETS_DIR):
        print(f"❌ 资源目录不存在: {ASSETS_DIR}")
        return
    
    # 获取所有图片
    images = [f for f in os.listdir(ASSETS_DIR) if f.endswith('.png')]
    
    if not images:
        print(f"⚠️  资源目录为空: {ASSETS_DIR}")
        return
    
    print(f"\n📁 资源目录: {ASSETS_DIR}")
    print(f"📊 图片数量: {len(images)}\n")
    
    # 测试每张图片
    results = []
    for img_name in sorted(images):
        print(f"🔍 测试: {img_name}")
        
        # 尝试不同阈值
        thresholds = [0.9, 0.8, 0.7, 0.6, 0.5]
        found_at = None
        
        for threshold in thresholds:
            result = find_image_on_screen(img_name, confidence=threshold)
            if result:
                found_at = threshold
                x, y, scale = result
                print(f"   ✅ 阈值 {threshold:.1f}: 找到 | 坐标:({x},{y}) | 尺度:{scale:.2f}")
                break
        
        if not found_at:
            print(f"   ❌ 未找到（所有阈值都失败）")
            results.append((img_name, None, None))
        else:
            results.append((img_name, found_at, result))
        
        print()
    
    # 统计结果
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    found_count = sum(1 for _, threshold, _ in results if threshold is not None)
    
    print(f"\n总计: {len(images)} 张图片")
    print(f"找到: {found_count} 张 ({found_count/len(images)*100:.1f}%)")
    print(f"未找到: {len(images) - found_count} 张\n")
    
    # 按阈值分组
    threshold_groups = {}
    for img_name, threshold, _ in results:
        if threshold:
            if threshold not in threshold_groups:
                threshold_groups[threshold] = []
            threshold_groups[threshold].append(img_name)
    
    if threshold_groups:
        print("按阈值分组:")
        for threshold in sorted(threshold_groups.keys(), reverse=True):
            imgs = threshold_groups[threshold]
            print(f"  阈值 {threshold:.1f}: {len(imgs)} 张")
            for img in imgs:
                print(f"    - {img}")
    
    # 未找到的图片
    not_found = [img for img, threshold, _ in results if threshold is None]
    if not_found:
        print(f"\n⚠️  未找到的图片 ({len(not_found)} 张):")
        for img in not_found:
            print(f"  - {img}")
        print("\n建议:")
        print("  1. 确保游戏界面显示这些按钮")
        print("  2. 重新截图，确保清晰完整")
        print("  3. 检查游戏分辨率是否变化")

def test_single_image(img_name):
    """测试单张图片"""
    print(f"🔍 测试图片: {img_name}\n")
    
    img_path = os.path.join(ASSETS_DIR, img_name)
    if not os.path.exists(img_path):
        print(f"❌ 图片不存在: {img_path}")
        return
    
    # 显示图片信息
    img = cv2.imread(img_path)
    if img is not None:
        h, w = img.shape[:2]
        print(f"图片尺寸: {w}x{h}")
        print(f"图片路径: {img_path}\n")
    
    # 测试不同阈值
    print("测试不同阈值:")
    print("-" * 40)
    
    thresholds = [0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5]
    
    for threshold in thresholds:
        result = find_image_on_screen(img_name, confidence=threshold)
        if result:
            x, y, scale = result
            print(f"阈值 {threshold:.2f}: ✅ 找到 | 坐标:({x},{y}) | 尺度:{scale:.2f}")
        else:
            print(f"阈值 {threshold:.2f}: ❌ 未找到")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 测试单张图片
        img_name = sys.argv[1]
        test_single_image(img_name)
    else:
        # 测试所有图片
        test_all_images()
