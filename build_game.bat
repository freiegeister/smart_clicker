@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 游戏打包脚本 (Windows)
REM 用法: build_game.bat <游戏名> [平台]
REM 平台: mac, win, all (默认: win)

if "%~1"=="" (
    echo ❌ 错误: 请指定游戏名
    echo.
    echo 用法: build_game.bat ^<游戏名^> [平台]
    echo.
    echo 可用游戏:
    dir /b games 2>nul
    echo.
    echo 平台选项:
    echo   mac       - 仅打包 macOS ^(Intel + ARM^)
    echo   win       - 仅打包 Windows ^(默认^)
    echo   all       - 打包所有平台
    echo.
    echo 示例:
    echo   build_game.bat 斗破奇兵
    echo   build_game.bat 斗破奇兵 win
    exit /b 1
)

set GAME_NAME=%~1
set PLATFORM=%~2
if "%PLATFORM%"=="" set PLATFORM=win

set GAME_DIR=games\%GAME_NAME%

REM 检查游戏是否存在
if not exist "%GAME_DIR%" (
    echo ❌ 错误: 游戏 '%GAME_NAME%' 不存在
    echo.
    echo 可用游戏:
    dir /b games 2>nul
    exit /b 1
)

REM 检查配置文件
if not exist "%GAME_DIR%\config.json" (
    echo ❌ 错误: 游戏配置文件不存在: %GAME_DIR%\config.json
    exit /b 1
)

echo ========================================
echo 🎮 开始打包游戏: %GAME_NAME%
echo ========================================
echo.

REM 1. 加载游戏到 current_game
echo 📦 步骤 1/4: 加载游戏配置...
python game_manager.py load "%GAME_NAME%"
if errorlevel 1 (
    echo ❌ 加载游戏失败
    exit /b 1
)
echo.

REM 2. 检查 Python 依赖
echo 🔍 步骤 2/4: 检查 Python 依赖...
if not exist "venv" (
    echo ❌ 错误: venv 不存在，请先创建虚拟环境
    echo 运行: python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
    exit /b 1
)

call venv\Scripts\activate
python -c "import cv2; import pyautogui; import mss; print('✅ 依赖检查通过')" 2>nul
if errorlevel 1 (
    echo ❌ 错误: Python 依赖不完整
    echo 运行: venv\Scripts\activate ^&^& pip install -r requirements.txt
    exit /b 1
)
echo.

REM 3. 更新 package.json 中的游戏名称
echo ⚙️  步骤 3/4: 更新打包配置...
cd electron

python -c "import json; import sys; sys.path.insert(0, '..'); config = json.load(open('../current_game/config.json', 'r', encoding='utf-8')); pkg = json.load(open('package.json', 'r', encoding='utf-8')); pkg['build']['productName'] = config.get('game_name', 'SmartClicker'); json.dump(pkg, open('package.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False); print('✅ 已设置应用名称:', config.get('game_name', 'SmartClicker'))"
echo.

REM 4. 执行打包
echo 🚀 步骤 4/4: 开始打包 (%PLATFORM%)...
echo ⏳ 这可能需要 5-15 分钟，请耐心等待...
echo.

if "%PLATFORM%"=="mac" (
    call npm run build:mac
) else if "%PLATFORM%"=="win" (
    call npm run build:win
) else if "%PLATFORM%"=="all" (
    call npm run build:all
) else (
    echo ❌ 错误: 未知平台 '%PLATFORM%'
    echo 支持的平台: mac, win, all
    exit /b 1
)

if errorlevel 1 (
    echo.
    echo ❌ 打包失败
    exit /b 1
)

cd ..

REM 5. 显示结果
echo.
echo ========================================
echo ✅ 打包完成！
echo ========================================
echo.
echo 输出目录: electron\dist\
echo.
echo 生成的文件:
dir /b electron\dist\*.exe electron\dist\*.dmg 2>nul
echo.
echo 💡 提示:
echo   - 将 .dmg 文件发给 macOS 用户
echo   - 将 .exe 文件发给 Windows 用户
echo.
