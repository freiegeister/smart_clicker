#!/bin/bash

# 游戏打包脚本
# 直接从 games/ 目录打包，不影响 current_game/
# 用法: ./build_game.sh <游戏名> [平台]
# 平台: mac, win, all (默认: all)

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查参数
if [ -z "$1" ]; then
    echo -e "${RED}❌ 错误: 请指定游戏名${NC}"
    echo ""
    echo "用法: ./build_game.sh <游戏名> [平台]"
    echo ""
    echo "可用游戏:"
    ls -1 games/ 2>/dev/null || echo "  (games/ 目录为空)"
    echo ""
    echo "平台选项:"
    echo "  mac       - 仅打包 macOS (当前架构)"
    echo "  mac-intel - 仅打包 macOS Intel"
    echo "  mac-arm   - 仅打包 macOS ARM"
    echo "  win       - 仅打包 Windows"
    echo "  all       - 打包所有平台 (默认)"
    echo ""
    echo "示例:"
    echo "  ./build_game.sh 斗破奇兵"
    echo "  ./build_game.sh 斗破奇兵 mac"
    echo "  ./build_game.sh 斗破奇兵 win"
    echo ""
    echo "注意: 此脚本直接从 games/ 打包，不会修改 current_game/"
    exit 1
fi

GAME_NAME="$1"
PLATFORM="${2:-all}"
GAME_DIR="games/$GAME_NAME"

# 检查游戏是否存在
if [ ! -d "$GAME_DIR" ]; then
    echo -e "${RED}❌ 错误: 游戏 '$GAME_NAME' 不存在${NC}"
    echo ""
    echo "可用游戏:"
    ls -1 games/ 2>/dev/null || echo "  (games/ 目录为空)"
    exit 1
fi

# 检查配置文件
if [ ! -f "$GAME_DIR/config.json" ]; then
    echo -e "${RED}❌ 错误: 游戏配置文件不存在: $GAME_DIR/config.json${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎮 开始打包游戏: $GAME_NAME${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 1. 检查 Python 依赖
echo -e "${YELLOW}🔍 步骤 1/4: 检查 Python 依赖...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 错误: venv 不存在，请先创建虚拟环境${NC}"
    echo "运行: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

source venv/bin/activate
python -c "import cv2; import pyautogui; import mss; print('✅ 依赖检查通过')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 错误: Python 依赖不完整${NC}"
    echo "运行: source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi
deactivate
echo ""

# 2. 创建临时打包目录
echo -e "${YELLOW}📦 步骤 2/4: 准备打包目录...${NC}"
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
echo -e "${YELLOW}⚙️  步骤 3/4: 更新打包配置...${NC}"
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

# 4. 执行打包
echo -e "${YELLOW}🚀 步骤 4/4: 开始打包 ($PLATFORM)...${NC}"
echo -e "${YELLOW}⏳ 这可能需要 5-15 分钟，请耐心等待...${NC}"
echo ""

BUILD_SUCCESS=true

case "$PLATFORM" in
    mac)
        npm run build:mac || BUILD_SUCCESS=false
        ;;
    mac-intel)
        npm run build:mac-intel || BUILD_SUCCESS=false
        ;;
    mac-arm)
        npm run build:mac-arm || BUILD_SUCCESS=false
        ;;
    win)
        npm run build:win || BUILD_SUCCESS=false
        ;;
    all)
        npm run build:all || BUILD_SUCCESS=false
        ;;
    *)
        echo -e "${RED}❌ 错误: 未知平台 '$PLATFORM'${NC}"
        echo "支持的平台: mac, mac-intel, mac-arm, win, all"
        BUILD_SUCCESS=false
        ;;
esac

# 清理
echo ""
echo -e "${YELLOW}🧹 清理临时文件...${NC}"

# 恢复 package.json
mv package.json.backup package.json
echo "✅ 已恢复 package.json"

cd ..

# 删除临时目录
rm -rf "$TEMP_PACK_DIR"
echo "✅ 已删除临时目录"

if [ "$BUILD_SUCCESS" = false ]; then
    echo ""
    echo -e "${RED}❌ 打包失败${NC}"
    exit 1
fi

# 5. 显示结果
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 打包完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}游戏名称:${NC} $DISPLAY_NAME"
echo -e "${GREEN}源目录:${NC} $GAME_DIR"
echo -e "${GREEN}输出目录:${NC} electron/dist/"
echo ""
echo -e "${GREEN}生成的文件:${NC}"
ls -lh electron/dist/ | grep -E '\.(dmg|exe)$' | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo -e "${YELLOW}💡 提示:${NC}"
echo "  - 将 .dmg 文件发给 macOS 用户"
echo "  - 将 .exe 文件发给 Windows 用户"
echo "  - current_game/ 目录未被修改"
echo ""
