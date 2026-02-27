# Smart Clicker - 智能游戏自动化工具

基于图片识别和 OCR 文字识别的自动化点击工具。

## 快速开始

### 1. 安装依赖
```bash
pip install PySide6 opencv-python pyautogui mss pillow easyocr
```

### 2. 运行
```bash
python gui.py
```

### 3. 使用流程
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

### 单游戏模式（推荐）
```bash
python gui.py                    # 直接使用，配置保存在 current_game/
```

### 多游戏模式
```bash
# 创建游戏
python manage_games.py create 游戏名

# 加载游戏
python manage_games.py load 游戏名

# 保存游戏
python manage_games.py export 游戏名

# 打包发布
python build_package.py 游戏名
```

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

```bash
# 检查配置和图片
python check_config.py

# 测试图片识别
python test_recognition.py

# 恢复丢失的数据
python recover_data.py
```

## 常见问题

**Q: 识别不到图片？**
- 运行 `python test_recognition.py` 诊断
- 降低置信度（confidence: 0.5）
- 重新截图

**Q: 没有点击行为？**
- 检查配置：`python check_config.py`
- 查看日志：`debug.log`
- 确保图片在 `current_game/assets/` 或 `assets/`

**Q: 数据丢失？**
- 运行 `python recover_data.py` 尝试恢复

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
└── games/                 # 游戏库（备份和管理多个游戏）
    └── 游戏名/
        ├── config.json
        └── assets/
```

**说明：**
- 所有截图和配置都保存在 `current_game/`
- `games/` 用于备份和管理多个游戏
- 根目录的 `config.json` 和 `assets/` 已废弃

## 技术栈

- Python 3.9+
- PySide6 (GUI)
- OpenCV (图像识别)
- PyAutoGUI (鼠标控制)
- MSS (屏幕截图)
- EasyOCR (文字识别，可选)
