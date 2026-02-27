#!/bin/bash

echo "================================"
echo "安装 OCR 文字识别功能"
echo "================================"
echo ""
echo "OCR 功能用于文字匹配模式："
echo "• 当图片识别不成功时使用"
echo "• 手动输入文字，引擎通过 OCR 在屏幕上找到并点击"
echo "• 适合按钮样式经常变化的游戏"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 错误：未找到虚拟环境"
    echo "请先运行以下命令创建虚拟环境："
    echo "  python3 -m venv venv"
    exit 1
fi

echo "✅ 找到虚拟环境"
echo ""

# 激活虚拟环境
echo "⏳ 激活虚拟环境..."
source venv/bin/activate

# 安装 easyocr
echo "⏳ 安装 easyocr（这可能需要几分钟）..."
pip install easyocr

if [ $? -eq 0 ]; then
    echo ""
    echo "================================"
    echo "✅ OCR 功能安装成功！"
    echo "================================"
    echo ""
    echo "使用方法："
    echo "1. 启动 GUI: python gui.py"
    echo "2. 点击 '🔤 添加文字规则'"
    echo "3. 输入要识别的文字（如'关闭'、'确定'）"
    echo "4. 启动引擎"
    echo ""
    echo "注意："
    echo "• 首次使用会自动下载识别模型（约 60MB）"
    echo "• 需要网络连接"
    echo "• 文字识别速度较慢（1-3秒）"
    echo "• 建议优先使用图片匹配，文字匹配作为备选"
    echo ""
else
    echo ""
    echo "❌ 安装失败"
    echo "请检查网络连接或手动安装："
    echo "  pip install easyocr"
    exit 1
fi
