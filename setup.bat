@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM Smart Clicker 一键安装脚本 (Windows)
REM 用法: 双击运行

echo.
echo 🚀 Smart Clicker 一键安装
echo ========================
echo.

REM 配置
set "INSTALL_DIR=%USERPROFILE%\SmartClicker"
set "ZIP_FILE=%~dp0smart-clicker-release.zip"

REM 检查 Python
echo 🔍 检查环境...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Python 3
    echo.
    echo 请先安装 Python 3.9+:
    echo   https://www.python.org/downloads/
    echo.
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION%

REM 检查是否已安装
if exist "%INSTALL_DIR%" (
    echo.
    echo ⚠️  检测到已安装，选择操作：
    echo   1^) 重新安装（覆盖）
    echo   2^) 直接启动
    echo   3^) 取消
    set /p choice="请选择 (1/2/3): "
    
    if "!choice!"=="1" (
        echo 🗑️  删除旧版本...
        rmdir /s /q "%INSTALL_DIR%"
    ) else if "!choice!"=="2" (
        echo 🚀 启动现有版本...
        cd /d "%INSTALL_DIR%"
        call venv\Scripts\activate.bat
        python gui.py
        exit /b 0
    ) else (
        echo ❌ 取消
        exit /b 0
    )
)

REM 创建安装目录
echo.
echo 📁 安装位置: %INSTALL_DIR%
mkdir "%INSTALL_DIR%" 2>nul
cd /d "%INSTALL_DIR%"

REM 检查压缩包
if not exist "%ZIP_FILE%" (
    echo ❌ 找不到压缩包: %ZIP_FILE%
    echo.
    echo 请确保 smart-clicker-release.zip 与此脚本在同一目录
    pause
    exit /b 1
)

echo.
echo 📦 解压文件...

REM 使用 PowerShell 解压并处理中文文件名
powershell -Command "& {[System.Text.Encoding]::Default = [System.Text.Encoding]::UTF8; Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::ExtractToDirectory('%ZIP_FILE%', '.', $true)}"

if %errorlevel% neq 0 (
    echo ⚠️  尝试备用解压方法...
    powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '.' -Force"
)

REM 如果解压出了子目录，移动文件到当前目录
if exist "smart-clicker-release" (
    xcopy "smart-clicker-release\*" "." /E /Y /Q >nul 2>&1
    rmdir /s /q "smart-clicker-release" 2>nul
)

echo ✅ 文件解压完成

REM 创建虚拟环境
echo.
echo 🔧 创建虚拟环境...
python -m venv venv

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo.
echo 📦 安装依赖（需要几分钟）...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ✅ 依赖安装完成

REM 创建启动脚本
echo @echo off > run.bat
echo cd /d "%%~dp0" >> run.bat
echo call venv\Scripts\activate.bat >> run.bat
echo python gui.py >> run.bat
echo deactivate >> run.bat

REM 创建桌面快捷方式
echo.
echo 📌 创建桌面快捷方式...

set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\SmartClicker.bat"

echo @echo off > "%SHORTCUT%"
echo cd /d "%INSTALL_DIR%" >> "%SHORTCUT%"
echo call run.bat >> "%SHORTCUT%"

echo ✅ 桌面快捷方式已创建

REM 创建卸载脚本
echo @echo off > uninstall.bat
echo echo ⚠️  确认卸载 Smart Clicker？(Y/N) >> uninstall.bat
echo set /p confirm= >> uninstall.bat
echo if /i "%%confirm%%"=="Y" ( >> uninstall.bat
echo     rmdir /s /q "%INSTALL_DIR%" >> uninstall.bat
echo     del "%DESKTOP%\SmartClicker.bat" >> uninstall.bat
echo     echo ✅ 已卸载 >> uninstall.bat
echo ) else ( >> uninstall.bat
echo     echo ❌ 取消 >> uninstall.bat
echo ) >> uninstall.bat
echo pause >> uninstall.bat

REM 完成
echo.
echo ✅ 安装完成！
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 启动方式：
echo   • 双击桌面的 SmartClicker.bat
echo   • 或运行: %INSTALL_DIR%\run.bat
echo.
echo 卸载方式：
echo   • 运行: %INSTALL_DIR%\uninstall.bat
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM 询问是否立即启动
set /p start_now="是否立即启动？(Y/N): "
if /i "%start_now%"=="Y" (
    echo.
    echo 🚀 启动中...
    python gui.py
)

pause
