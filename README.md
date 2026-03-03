# Smart Clicker - 智能游戏自动化工具

基于图片识别的自动化点击工具。

## 快速开始

### 开发环境

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 运行
```bash
python gui.py
```

### 打包发布

1. 进入 Electron 目录
```bash
cd electron
```

2. 安装依赖（首次）
```bash
npm install
```

3. 打包应用
```bash
npm run build
```

4. 输出文件
- macOS: `dist/SmartClicker-1.0.0.dmg`
- Windows: `dist/SmartClicker-1.0.0.exe`

用户无需安装 Python，开箱即用。

## 使用流程
1. 点击「📷 截图添加素材」，截取游戏按钮
2. 选择按钮类型（干扰弹窗、关闭、打开等）
3. 点击「▶ 启动挂机引擎」

## 策略说明

| 策略 | 优先级 | 说明 |
|-----|-------|------|
| 干扰弹窗 | 最高 | 见到就点，立即关闭 |
| 关闭后置条件 | 高 | 点击关闭后的二次确认 |
| 关闭 | 中 | 需要满足前置条件才点击 |
| 打开 | 低 | 主动点击观看广告、领取奖励 |
| 关闭前置条件 | - | 仅用于检测，不点击 |

## 游戏管理

### 开发模式
```bash
python gui.py                    # 直接使用，配置保存在 current_game/
```

### 打包发布
```bash
cd electron
npm install                      # 首次需要安装依赖
npm run build                    # 打包成独立应用
```

打包后输出：
- macOS: `electron/dist/SmartClicker-1.0.0.dmg`
- Windows: `electron/dist/SmartClicker-1.0.0.exe`

用户无需安装 Python，开箱即用。

## 配置说明

配置文件：`current_game/config.json` 或 `config.json`

```json
{
  "strategies": [
    {
      "name": "干扰弹窗",
      "trigger_images": ["popup_123.png"],
      "confidence": 0.75,
      "post_delay": 0.5
    }
  ],
  "settings": {
    "idle_timeout": 300,
    "scan_interval": 0.5
  }
}
```

## 诊断工具

开发模式下可以使用以下工具：

```bash
# 测试所有图片的识别效果
python test_recognition.py

# 测试单张图片
python test_recognition.py popup_1772125941.png

# 其他诊断工具
python 诊断识别问题.py
python 对比测试.py
```

## 常见问题

**Q: 识别不到图片？**
- 运行 `python test_recognition.py` 查看所有图片的识别效果
- 查看日志中的匹配分数，如果接近 0.7 可以降低阈值
- 如果分数 < 0.6，需要重新截图
- 确保游戏界面显示目标按钮

**Q: 没有点击行为？**
- 查看日志：`debug.log`
- 确保图片在 `current_game/assets/`
- 检查策略是否启用
- 检查是否满足前置条件

**Q: 如何打包发布？**
- 进入 `electron/` 目录
- 运行 `npm run build`
- 分发生成的 .dmg 或 .exe 文件

**Q: 识别算法可靠吗？**
- 使用 OpenCV 灰度模板匹配
- 匹配分数通常 0.8-0.95（高）
- 支持 85%-100% 的尺寸变化
- 详见 `RECOGNITION_ANALYSIS.md`

## 目录结构

```
smart_clicker/
├── gui.py                 # 图形界面
├── main.py                # 核心引擎
├── game_manager.py        # 游戏管理
├── config_default.json    # 默认配置模板
│
├── current_game/          # 工作目录（所有操作都在这里）
│   ├── config.json        # 当前配置
│   └── assets/            # 当前图片资源
│
├── games/                 # 游戏库（备份和管理多个游戏）
│   └── 游戏名/
│       ├── config.json
│       └── assets/
│
└── electron/              # Electron 打包目录
    ├── main.js            # Electron 主进程
    ├── index.html         # 界面
    ├── package.json       # 打包配置
    └── dist/              # 打包输出
```

**说明：**
- 所有截图和配置都保存在 `current_game/`
- `games/` 用于备份和管理多个游戏
- `electron/` 用于打包成独立应用

## 技术栈

- Python 3.9+
- PySide6 (GUI)
- OpenCV (图像识别)
- PyAutoGUI (鼠标控制)
- MSS (屏幕截图)
- Electron (打包)
- EasyOCR (文字识别，可选)
