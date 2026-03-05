#!/bin/bash

# 跨平台打包脚本
# 直接从 games/ 目录打包，不影响 current_game/
# 打包当前架构的 macOS + Windows 版本

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${RED}❌ 错误: 请指定游戏名${NC}"
    echo ""
    echo "用法: ./build_cross_platform.sh <游戏名>"
    echo ""
    echo "可用游戏:"
    ls -1 games/ 2>/dev/null || echo "  (games/ 目录为空)"
    echo ""
    echo "此脚本会打包："
    echo "  - 当前架构的 macOS 版本"
    echo "  - Windows x64 版本"
    echo ""
    echo "注意: 直接从 games/ 打包，不会修改 current_game/"
    exit 1
fi

GAME_NAME="$1"
GAME_DIR="games/$GAME_NAME"

if [ ! -d "$GAME_DIR" ]; then
    echo -e "${RED}❌ 错误: 游戏 '$GAME_NAME' 不存在${NC}"
    exit 1
fi

if [ ! -f "$GAME_DIR/config.json" ]; then
    echo -e "${RED}❌ 错误: 游戏配置文件不存在: $GAME_DIR/config.json${NC}"
    exit 1
fi

CURRENT_ARCH=$(uname -m)

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎮 跨平台打包: $GAME_NAME${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}当前架构: $CURRENT_ARCH${NC}"
echo -e "${YELLOW}将打包: macOS ($CURRENT_ARCH) + Windows (x64)${NC}"
echo -e "${YELLOW}源目录: $GAME_DIR${NC}"
echo ""

# 1. 检查 Python 依赖
echo -e "${YELLOW}🔍 步骤 1/5: 检查 Python 依赖...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 错误: venv 不存在${NC}"
    echo "运行: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

source venv/bin/activate
python -c "import cv2; import pyautogui; import mss; print('✅ Python 依赖检查通过')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 错误: Python 依赖不完整${NC}"
    exit 1
fi
deactivate
echo ""

# 2. 创建临时打包目录
echo -e "${YELLOW}📦 步骤 2/5: 准备打包目录...${NC}"
TEMP_PACK_DIR=".pack_temp_$GAME_NAME"

# 清理旧的临时目录
if [ -d "$TEMP_PACK_DIR" ]; then
    rm -rf "$TEMP_PACK_DIR"
fi

# 复制游戏配置到临时目录
mkdir -p "$TEMP_PACK_DIR"
cp -r "$GAME_DIR"/* "$TEMP_PACK_DIR/"

echo -e "${GREEN}✅ 已复制游戏配置到临时目录${NC}"
echo ""

# 3. 更新 package.json
echo -e "${YELLOW}⚙️  步骤 3/5: 更新打包配置...${NC}"
cd electron

# 读取游戏名称
DISPLAY_NAME=$(python3 -c "
import json
with open('../$TEMP_PACK_DIR/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    print(config.get('game_name', 'SmartClicker'))
")

# 备份原始 package.json
cp package.json package.json.backup

# 更新 package.json
python3 -c "
import json
with open('package.json', 'r', encoding='utf-8') as f:
    pkg = json.load(f)

# 更新应用名称
pkg['build']['productName'] = '$DISPLAY_NAME'

# 更新 extraResources，指向临时目录
pkg['build']['extraResources'] = [
    {
        'from': '../venv',
        'to': 'python_app/venv'
    },
    {
        'from': '../',
        'to': 'python_app',
        'filter': [
            'main.py',
            'game_manager.py'
        ]
    },
    {
        'from': '../$TEMP_PACK_DIR',
        'to': 'python_app/current_game'
    }
]

with open('package.json', 'w', encoding='utf-8') as f:
    json.dump(pkg, f, indent=2, ensure_ascii=False)

print('✅ 已设置应用名称: $DISPLAY_NAME')
print('✅ 已配置打包源: $TEMP_PACK_DIR')
"
echo ""

# 4. 打包 macOS (当前架构)
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🍎 打包 macOS ($CURRENT_ARCH)...${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

npm run build:mac

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ macOS 打包失败${NC}"
    # 恢复 package.json
    mv package.json.backup package.json
    cd ..
    rm -rf "$TEMP_PACK_DIR"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ macOS 打包完成${NC}"
echo ""

# 5. 打包 Windows
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🪟 打包 Windows (x64)...${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}⏳ 这可能需要 10-20 分钟（首次需要下载 Windows 依赖）...${NC}"
echo ""

npm run build:win

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Windows 打包失败${NC}"
    # 恢复 package.json
    mv package.json.backup package.json
    cd ..
    rm -rf "$TEMP_PACK_DIR"
    exit 1
fi

# 6. 清理
echo ""
echo -e "${YELLOW}🧹 步骤 5/5: 清理临时文件...${NC}"

# 恢复 package.json
mv package.json.backup package.json
echo "✅ 已恢复 package.json"

cd ..

# 删除临时目录
rm -rf "$TEMP_PACK_DIR"
echo "✅ 已删除临时目录"
echo ""

# 7. 显示结果
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 跨平台打包完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}游戏名称:${NC} $DISPLAY_NAME"
echo -e "${GREEN}源目录:${NC} $GAME_DIR"
echo -e "${GREEN}输出目录:${NC} electron/dist/"
echo ""
echo -e "${GREEN}生成的文件:${NC}"
ls -lh electron/dist/*.{dmg,exe} 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo -e "${YELLOW}💡 发布说明:${NC}"
echo "  📱 macOS ($CURRENT_ARCH) 用户: .dmg 文件"
if [ "$CURRENT_ARCH" = "arm64" ]; then
    echo "     ℹ️  Intel Mac 用户可以通过 Rosetta 2 运行此版本"
elif [ "$CURRENT_ARCH" = "x86_64" ]; then
    echo "     ℹ️  ARM Mac 用户无法运行此版本，需要 ARM 版本"
fi
echo "  🪟 Windows 用户: .exe 安装程序"
echo ""
echo -e "${YELLOW}📝 注意:${NC}"
echo "  - current_game/ 目录未被修改"
echo "  - 打包使用的是 $GAME_DIR 的配置"
echo "  - macOS 版本仅支持 $CURRENT_ARCH 架构"
echo ""
