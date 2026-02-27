#!/usr/bin/env python3
"""
打包脚本
将指定游戏打包为独立应用
"""
import os
import sys
import shutil
import argparse
from game_manager import GameManager

def build_package(game_name, output_dir="dist"):
    """
    打包指定游戏
    
    Args:
        game_name: 游戏名称
        output_dir: 输出目录
    """
    manager = GameManager()
    
    print(f"🎮 开始打包游戏: {game_name}")
    print("=" * 50)
    
    # 1. 加载游戏到 current_game
    print("\n📦 步骤 1: 加载游戏配置...")
    try:
        manager.load_game_to_current(game_name)
    except ValueError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
    
    # 2. 检查必要文件
    print("\n📋 步骤 2: 检查必要文件...")
    required_files = [
        "gui.py",
        "main.py",
        "snipper.py",
        "game_manager.py",
        "current_game/config.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少必要文件:")
        for file in missing_files:
            print(f"   - {file}")
        sys.exit(1)
    
    print("✅ 所有必要文件都存在")
    
    # 3. 创建输出目录
    print(f"\n📁 步骤 3: 创建输出目录...")
    package_dir = os.path.join(output_dir, game_name)
    if os.path.exists(package_dir):
        print(f"⚠️  目录已存在，将被覆盖: {package_dir}")
        shutil.rmtree(package_dir)
    
    os.makedirs(package_dir, exist_ok=True)
    print(f"✅ 创建目录: {package_dir}")
    
    # 4. 复制核心文件
    print("\n📄 步骤 4: 复制核心文件...")
    core_files = [
        "gui.py",
        "main.py",
        "snipper.py",
        "game_manager.py",
        "config_default.json"
    ]
    
    for file in core_files:
        if os.path.exists(file):
            shutil.copy(file, os.path.join(package_dir, file))
            print(f"   ✓ {file}")
    
    # 5. 复制游戏配置和资源
    print("\n🎮 步骤 5: 复制游戏配置和资源...")
    
    # 复制 current_game 目录
    current_game_src = "current_game"
    current_game_dst = os.path.join(package_dir, "current_game")
    
    if os.path.exists(current_game_src):
        shutil.copytree(current_game_src, current_game_dst)
        print(f"   ✓ current_game/")
        
        # 统计资源文件
        assets_dir = os.path.join(current_game_dst, "assets")
        if os.path.exists(assets_dir):
            asset_count = len([f for f in os.listdir(assets_dir) if f.endswith('.png')])
            print(f"   ✓ 包含 {asset_count} 个图片资源")
    
    # 6. 创建启动脚本
    print("\n🚀 步骤 6: 创建启动脚本...")
    
    # Windows 启动脚本
    with open(os.path.join(package_dir, "start.bat"), 'w', encoding='utf-8') as f:
        f.write(f"""@echo off
chcp 65001 > nul
title {game_name} - Smart Clicker
echo 正在启动 {game_name}...
python gui.py
pause
""")
    print("   ✓ start.bat (Windows)")
    
    # macOS/Linux 启动脚本
    with open(os.path.join(package_dir, "start.sh"), 'w', encoding='utf-8') as f:
        f.write(f"""#!/bin/bash
echo "正在启动 {game_name}..."
python3 gui.py
""")
    os.chmod(os.path.join(package_dir, "start.sh"), 0o755)
    print("   ✓ start.sh (macOS/Linux)")
    
    # 7. 创建 README
    print("\n📝 步骤 7: 创建说明文档...")
    with open(os.path.join(package_dir, "README.txt"), 'w', encoding='utf-8') as f:
        f.write(f"""
{game_name} - Smart Clicker
{'=' * 50}

安装依赖:
  pip install PySide6 opencv-python pyautogui mss pillow easyocr

运行程序:
  Windows: 双击 start.bat
  macOS/Linux: ./start.sh
  或直接运行: python gui.py

目录结构:
  current_game/config.json  - 游戏配置
  current_game/assets/      - 图片资源
  gui.py                    - 图形界面
  main.py                   - 核心引擎

注意事项:
  1. 首次运行需要安装依赖
  2. OCR 功能首次使用会下载模型（约 100MB）
  3. 需要授予屏幕录制权限（macOS）
  4. 修改配置后会自动保存

打包时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
    print("   ✓ README.txt")
    
    # 8. 创建 requirements.txt
    with open(os.path.join(package_dir, "requirements.txt"), 'w') as f:
        f.write("""PySide6>=6.5.0
opencv-python>=4.8.0
pyautogui>=0.9.54
mss>=9.0.1
pillow>=10.0.0
easyocr>=1.7.0
""")
    print("   ✓ requirements.txt")
    
    # 9. 完成
    print("\n" + "=" * 50)
    print(f"✅ 打包完成！")
    print(f"\n📦 输出目录: {os.path.abspath(package_dir)}")
    print(f"\n📊 打包统计:")
    
    # 统计文件大小
    total_size = 0
    file_count = 0
    for root, dirs, files in os.walk(package_dir):
        for file in files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)
            file_count += 1
    
    print(f"   文件数量: {file_count}")
    print(f"   总大小: {total_size / 1024 / 1024:.2f} MB")
    
    print(f"\n💡 下一步:")
    print(f"   1. 测试: cd {package_dir} && python gui.py")
    print(f"   2. 分发: 将 {package_dir} 目录打包发送")
    print(f"   3. 用户只需安装依赖后运行启动脚本")

def main():
    parser = argparse.ArgumentParser(description='打包游戏配置')
    parser.add_argument('game_name', help='游戏名称')
    parser.add_argument('--output', '-o', default='dist', help='输出目录（默认: dist）')
    
    args = parser.parse_args()
    
    build_package(args.game_name, args.output)

if __name__ == "__main__":
    main()
