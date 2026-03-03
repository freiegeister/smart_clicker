# Electron 打包指南

## 开发环境

```bash
python gui.py
```

## 打包步骤

### 1. 安装依赖（首次）

```bash
cd electron
npm install
```

### 2. 打包

```bash
npm run build
```

等待 5-10 分钟（正常）

### 3. 输出

```
dist/SmartClicker-1.0.0.dmg  ← 给用户这个文件
```

## 常见问题

### Q: 打包很慢？
A: 正常，需要压缩 1.5GB 的 Python 环境

### Q: 打包后找不到 cv2？
A: 确保 venv 中有 opencv-python
```bash
source venv/bin/activate
python -c "import cv2"
```

### Q: 给用户哪些文件？
A: 只给 `.dmg` 文件

## 就这么简单
