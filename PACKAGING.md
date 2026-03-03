# Electron 打包指南

## 前提条件

1. 确保已安装 Node.js (推荐 v18+)
2. 确保 Python 虚拟环境已配置（项目根目录的 venv/）
3. 确保 venv 中已安装所有依赖

```bash
# 检查 Python 环境
source venv/bin/activate
python -c "import cv2, numpy, pyautogui, mss; print('✅ 依赖完整')"
```

## 打包步骤

### 1. 准备游戏配置

确保 `current_game/` 目录包含：
- `config.json` - 游戏配置
- `assets/*.png` - 图片资源

### 2. 安装 Electron 依赖（首次）

```bash
cd electron
npm install
```

### 3. 打包应用

```bash
npm run build
```

等待 5-10 分钟（正常，需要压缩 Python 环境）

### 4. 输出文件

打包完成后，在 `electron/dist/` 目录找到：

- **macOS**: `SmartClicker-1.0.0.dmg`
- **Windows**: `SmartClicker-1.0.0.exe`

## 分发

只需要给用户 `.dmg` 或 `.exe` 文件，用户双击安装即可使用。

**无需**：
- Python 环境
- 依赖安装
- 配置文件

**已包含**：
- 完整的 Python 运行时
- 所有依赖库
- 游戏配置和资源

## 常见问题

### Q: 打包很慢？
A: 正常，需要压缩整个 Python 虚拟环境（约 200MB）

### Q: 打包后运行报错找不到模块？
A: 检查 venv 中是否安装了所有依赖
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Q: 如何修改应用名称？
A: 编辑 `electron/package.json` 中的 `productName` 字段

### Q: 如何修改应用图标？
A: 将图标文件放在 `electron/` 目录，并在 `package.json` 的 `build.mac.icon` 中配置

### Q: 打包后文件太大？
A: 正常，包含完整 Python 环境约 200-300MB

## 开发模式

在开发时，可以直接运行：

```bash
cd electron
npm start
```

这会启动 Electron 应用，调用项目根目录的 Python 脚本。

## 打包配置

关键配置在 `electron/package.json` 的 `build.extraResources`：

```json
"extraResources": [
  {
    "from": "../venv",
    "to": "python_app/venv"
  },
  {
    "from": "../",
    "to": "python_app",
    "filter": [
      "main.py",
      "game_manager.py",
      "current_game/**/*"
    ]
  }
]
```

这会将 Python 环境和必要文件打包到应用中。
