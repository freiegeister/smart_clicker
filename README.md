# Smart Clicker - 智能游戏自动化工具

基于图片识别的自动化点击工具。

## 快速开始

### 开发环境
创建虚拟环境
```
python3 -m venv ./venv
source venv/bin/activate
```

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 运行
```bash
python gui.py
```

### 打包压缩
```
./pack.sh 
```
输出smart-clicker-release.zip
该文件打包的是current_game下的游戏。

### 交付用户
把smart-clicker-release.zip和setup.sh（或setup.bat）交付给用户。
用户执行setup.sh即可。

## 策略说明

| 策略 | 优先级 | 说明 |
|-----|-------|------|
| 干扰弹窗 | 最高 | 见到就点，立即关闭 |
| 关闭后置条件 | 高 | 点击关闭后的二次确认 |
| 关闭 | 中 | 需要满足前置条件才点击 |
| 打开 | 低 | 主动点击观看广告、领取奖励 |
| 关闭前置条件 | - | 仅用于检测，不点击 |

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
- 当前游戏目录 `current_game/`
- `games/` 用于备份和管理多个游戏

## 技术栈

- Python 3.9+
- PySide6 (GUI)
- OpenCV (图像识别)
- PyAutoGUI (鼠标控制)
- MSS (屏幕截图)
- Electron (打包)
- EasyOCR (文字识别，可选)
