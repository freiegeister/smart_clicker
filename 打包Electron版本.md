# Electron 打包指南

## 快速开始

### 使用打包脚本（推荐）

**macOS/Linux:**
```bash
./build_game.sh <游戏名> [平台]
```

**Windows:**
```cmd
build_game.bat <游戏名> [平台]
```

**示例:**
```bash
# 打包"斗破奇兵"游戏，所有平台
./build_game.sh 斗破奇兵

# 仅打包 macOS 版本
./build_game.sh 斗破奇兵 mac

# 仅打包 Windows 版本
./build_game.sh 斗破奇兵 win
```

脚本会自动：
1. 加载指定游戏到 `current_game/`
2. 检查 Python 依赖
3. 更新应用名称为游戏名
4. 执行打包
5. 显示输出文件

---

## 手动打包步骤

### 1. 准备游戏配置

```bash
# 列出所有游戏
python game_manager.py list

# 加载指定游戏到 current_game/
python game_manager.py load 斗破奇兵
```

### 2. 安装依赖（首次）

```bash
cd electron
npm install
```

### 3. 打包

#### 打包所有平台
```bash
npm run build:all
```

#### 或分别打包

**macOS (Intel + ARM 通用版)**
```bash
npm run build:mac
```

**macOS (仅 Intel)**
```bash
npm run build:mac-intel
```

**macOS (仅 ARM/M1/M2)**
```bash
npm run build:mac-arm
```

**Windows**
```bash
npm run build:win
```

### 4. 输出文件

打包完成后，在 `electron/dist/` 目录下会生成：

```
dist/
├── <游戏名>-1.0.0-arm64.dmg          # macOS ARM (M1/M2/M3)
├── <游戏名>-1.0.0-x64.dmg            # macOS Intel
├── <游戏名>-1.0.0.dmg                # macOS 通用版
└── <游戏名> Setup 1.0.0.exe          # Windows 安装程序
```

**注意:** 应用名称会自动使用 `config.json` 中的 `game_name` 字段。

---

## 游戏管理

### 创建新游戏
```bash
python game_manager.py create 新游戏名
```

### 导出当前配置为游戏
```bash
python game_manager.py export 游戏名
```

### 加载游戏
```bash
python game_manager.py load 游戏名
```

### 列出所有游戏
```bash
python game_manager.py list
```

---

## 多游戏打包工作流

### 场景 1: 为不同游戏打包独立应用

```bash
# 打包游戏 A
./build_game.sh 游戏A all

# 打包游戏 B
./build_game.sh 游戏B all

# 结果：
# electron/dist/游戏A-1.0.0.dmg
# electron/dist/游戏A Setup 1.0.0.exe
# electron/dist/游戏B-1.0.0.dmg
# electron/dist/游戏B Setup 1.0.0.exe
```

### 场景 2: 批量打包多个游戏

**macOS/Linux:**
```bash
for game in games/*; do
    game_name=$(basename "$game")
    ./build_game.sh "$game_name" all
done
```

**Windows:**
```cmd
for /d %G in (games\*) do build_game.bat "%~nxG" win
```

---

## 跨平台打包说明

### 在 macOS 上打包
- ✅ 可以打包 macOS (Intel + ARM)
- ✅ 可以打包 Windows（需要安装 wine）
- 推荐：`./build_game.sh <游戏名> all`

### 在 Windows 上打包
- ✅ 可以打包 Windows
- ❌ 无法打包 macOS
- 推荐：`build_game.bat <游戏名> win`

### 在 Linux 上打包
- ✅ 可以打包 Windows（需要 wine）
- ❌ 无法打包 macOS
- 推荐：`./build_game.sh <游戏名> win`

---

## 注意事项

### Python 虚拟环境
打包前确保 venv 已正确安装所有依赖：

```bash
# macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
python -c "import cv2; import pyautogui; print('✅ 依赖正常')"

# Windows
venv\Scripts\activate
pip install -r requirements.txt
python -c "import cv2; import pyautogui; print('✅ 依赖正常')"
```

### 打包大小
- macOS: ~200-300MB（压缩后）
- Windows: ~150-250MB（安装程序）
- 打包时间: 5-15 分钟（取决于机器性能）

### Windows 特殊说明
Windows 版本会创建 NSIS 安装程序，用户可以：
- 选择安装位置
- 创建桌面快捷方式
- 创建开始菜单快捷方式

### 应用名称
- 应用名称自动从 `current_game/config.json` 的 `game_name` 字段读取
- 不同游戏会生成不同名称的安装包
- 用户可以同时安装多个游戏的应用

---

## 常见问题

### Q: 打包很慢？
A: 正常，需要压缩整个 Python 环境（包含 OpenCV 等大型库）

### Q: 打包后找不到 cv2？
A: 确保 venv 中已安装 opencv-python
```bash
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install opencv-python
```

### Q: Windows 打包失败？
A: 在 macOS 上打包 Windows 需要安装 wine：
```bash
brew install wine-stable
```

### Q: 如何区分不同游戏？
A: 
1. 每个游戏在 `games/` 目录下有独立文件夹
2. 使用 `build_game.sh` 脚本打包时会自动使用游戏名
3. 生成的安装包名称包含游戏名

### Q: 给用户哪些文件？
A: 
- macOS 用户：`.dmg` 文件
- Windows 用户：`.exe` 安装程序

### Q: 如何减小打包体积？
A: 
1. 使用 `pip install --no-cache-dir` 安装依赖
2. 删除 venv 中的 `__pycache__` 和 `.pyc` 文件
3. 只打包必要的平台

### Q: 可以同时安装多个游戏的应用吗？
A: 可以！每个游戏打包成独立应用，应用名称不同，可以同时安装。

---

## 发布清单

打包完成后，测试以下功能：

- [ ] 应用能正常启动
- [ ] 应用标题显示正确的游戏名
- [ ] 引擎能正常运行
- [ ] 图片识别功能正常
- [ ] 点击功能正常
- [ ] 日志显示正常
- [ ] 停止按钮正常工作

---

## 快速命令参考

```bash
# 使用打包脚本（推荐）
./build_game.sh 斗破奇兵           # 打包所有平台
./build_game.sh 斗破奇兵 mac       # 仅 macOS
./build_game.sh 斗破奇兵 win       # 仅 Windows

# 手动打包
cd electron
npm start                          # 开发测试
npm run build                      # 打包当前平台
npm run build:mac                  # 打包 macOS
npm run build:win                  # 打包 Windows
npm run build:all                  # 打包所有平台

# 游戏管理
python game_manager.py list        # 列出游戏
python game_manager.py load 游戏名  # 加载游戏
python game_manager.py export 游戏名 # 导出游戏
```
