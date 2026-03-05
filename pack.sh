#!/bin/bash

# 打包脚本 - 创建分发压缩包
# 只包含必要的文件，排除开发文件和用户数据

set -e

echo "📦 Smart Clicker 打包工具"
echo "========================="
echo ""

# 配置
OUTPUT_FILE="smart-clicker-release.zip"
TEMP_DIR="smart-clicker-release"

# 清理旧文件
echo "🧹 清理旧文件..."
rm -rf "$TEMP_DIR" "$OUTPUT_FILE"

# 创建临时目录
mkdir -p "$TEMP_DIR"

echo "📋 复制必要文件..."

# 复制 Python 文件
cp *.py "$TEMP_DIR/" 2>/dev/null || true

# 复制配置文件
cp config_default.json "$TEMP_DIR/" 2>/dev/null || true
cp requirements.txt "$TEMP_DIR/" 2>/dev/null || true

# 复制 current_game 目录（包含所有文件）
if [ -d "current_game" ]; then
    cp -r "current_game" "$TEMP_DIR/"
    echo "  ✅ current_game/ (包含所有文件)"
fi

# 复制安装脚本
cp setup.sh "$TEMP_DIR/" 2>/dev/null || true
cp setup.bat "$TEMP_DIR/" 2>/dev/null || true


# 统计文件
echo ""
echo "📊 打包内容："
echo "----------------------------------------"
find "$TEMP_DIR" -type f | while read file; do
    size=$(du -h "$file" | cut -f1)
    echo "  $size  ${file#$TEMP_DIR/}"
done
echo "----------------------------------------"

# 压缩
echo ""
echo "🗜️  压缩中..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS: 使用 ditto 保持 UTF-8 编码
    ditto -c -k --sequesterRsrc --keepParent "$TEMP_DIR" "$OUTPUT_FILE"
else
    # Linux: 使用 zip with UTF-8
    cd "$TEMP_DIR"
    zip -r -q "../$OUTPUT_FILE" .
    cd ..
fi

# 清理临时目录
rm -rf "$TEMP_DIR"

# 完成
FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
echo ""
echo "✅ 打包完成！"
echo ""
echo "输出文件: $OUTPUT_FILE"
echo "文件大小: $FILE_SIZE"