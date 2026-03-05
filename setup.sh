#!/bin/bash

# Smart Clicker 一键安装脚本 (macOS/Linux)
# 用法: ./setup.sh

set -e

echo "🚀 Smart Clicker 一键安装"
echo "========================"
echo ""

# 配置
INSTALL_DIR="$HOME/SmartClicker"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ZIP_FILE="$SCRIPT_DIR/smart-clicker-release.zip"

# 检测系统
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "❌ Windows 用户请使用 setup.bat"
    exit 1
fi

# 检查 Python
echo "🔍 检查环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3"
    echo ""
    echo "请先安装 Python 3.9+:"
    echo "  https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION"

# 检查是否已安装
if [ -d "$INSTALL_DIR" ]; then
    echo ""
    echo "⚠️  检测到已安装，选择操作："
    echo "  1) 重新安装（覆盖）"
    echo "  2) 直接启动"
    echo "  3) 取消"
    read -p "请选择 (1/2/3): " choice
    
    case $choice in
        1)
            echo "🗑️  删除旧版本..."
            rm -rf "$INSTALL_DIR"
            ;;
        2)
            echo "🚀 启动现有版本..."
            cd "$INSTALL_DIR"
            source venv/bin/activate 2>/dev/null || true
            python3 gui.py
            exit 0
            ;;
        *)
            echo "❌ 取消"
            exit 0
            ;;
    esac
fi

# 创建安装目录
echo ""
echo "📁 安装位置: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# 检查压缩包
if [ ! -f "$ZIP_FILE" ]; then
    echo "❌ 找不到压缩包: $ZIP_FILE"
    echo ""
    echo "请确保 smart-clicker-release.zip 与此脚本在同一目录"
    exit 1
fi

echo ""
echo "📦 解压文件..."

# 处理中文文件名
if [[ "$OSTYPE" == "darwin"* ]]; then
    if command -v ditto &> /dev/null; then
        ditto -xk "$ZIP_FILE" .
    else
        unzip -O UTF-8 -q "$ZIP_FILE" 2>/dev/null || unzip -q "$ZIP_FILE"
    fi
else
    unzip -O UTF-8 -q "$ZIP_FILE" 2>/dev/null || unzip -O GB18030 -q "$ZIP_FILE" 2>/dev/null || unzip -q "$ZIP_FILE"
fi

# 如果解压出了子目录，移动文件到当前目录
if [ -d "smart-clicker-release" ]; then
    mv smart-clicker-release/* . 2>/dev/null || true
    mv smart-clicker-release/.* . 2>/dev/null || true
    rm -rf smart-clicker-release
fi

echo "✅ 文件解压完成"

# 创建虚拟环境
echo ""
echo "🔧 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo ""
echo "📦 安装依赖（需要几分钟）..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "✅ 依赖安装完成"

# 创建启动脚本
cat > run.sh << 'RUNSCRIPT'
#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
source venv/bin/activate
python3 gui.py
deactivate
RUNSCRIPT

chmod +x run.sh

# 创建桌面快捷方式
DESKTOP="$HOME/Desktop"
if [ -d "$DESKTOP" ]; then
    cat > "$DESKTOP/SmartClicker.command" << SHORTCUT
#!/bin/bash
cd "$INSTALL_DIR"
./run.sh
SHORTCUT
    chmod +x "$DESKTOP/SmartClicker.command"
    echo "✅ 桌面快捷方式已创建"
fi

# 创建卸载脚本
cat > uninstall.sh << 'UNINSTALL'
#!/bin/bash
echo "⚠️  确认卸载 Smart Clicker？(y/n)"
read -r response
if [[ "$response" == "y" ]]; then
    rm -rf "$HOME/SmartClicker"
    rm -f "$HOME/Desktop/SmartClicker.command"
    echo "✅ 已卸载"
else
    echo "❌ 取消"
fi
UNINSTALL

chmod +x uninstall.sh

# 完成
echo ""
echo "✅ 安装完成！"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "启动方式："
echo "  • 双击桌面的 SmartClicker.command"
echo "  • 或运行: $INSTALL_DIR/run.sh"
echo ""
echo "卸载方式："
echo "  • 运行: $INSTALL_DIR/uninstall.sh"
echo ""
echo "首次运行需要授予权限："
echo "  系统偏好设置 → 安全性与隐私 → 隐私"
echo "  • 辅助功能 - 勾选 Terminal/Python"
echo "  • 屏幕录制 - 勾选 Terminal/Python"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 询问是否立即启动
read -p "是否立即启动？(y/n): " start_now
if [[ "$start_now" == "y" ]]; then
    echo ""
    echo "🚀 启动中..."
    python3 gui.py
fi
