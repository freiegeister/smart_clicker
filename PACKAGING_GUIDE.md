# 打包指南 - 完整说明

## 跨平台打包能力矩阵

| 打包机器 | 可打包 macOS ARM | 可打包 macOS Intel | 可打包 Windows | 推荐方案 |
|---------|-----------------|-------------------|---------------|---------|
| ARM Mac (M1/M2/M3) | ✅ 可靠 | ❌ 不可靠 | ✅ 可靠 | ARM Mac + Windows |
| Intel Mac | ❌ 不可靠 | ✅ 可靠 | ✅ 可靠 | Intel Mac + Windows |
| Windows | ❌ 不可以 | ❌ 不可以 | ✅ 可靠 | 仅 Windows |
| Linux | ❌ 不可以 | ❌ 不可以 | ✅ 可靠 | 仅 Windows |

### 为什么 macOS 跨架构打包不可靠？

**问题根源：**
- Python 的 C 扩展（numpy、opencv-python）是预编译的二进制文件
- ARM64 编译的 `.so` 文件无法在 Intel Mac 上运行
- Intel 编译的 `.so` 文件无法在 ARM Mac 上运行
- 虽然可以通过 Rosetta 创建跨架构 venv，但不稳定且难以测试

**为什么 Windows 打包可以？**
- Electron Builder 在打包 Windows 时会重新处理依赖
- 不会直接复制 macOS 的 venv
- Windows 的 Python 包是独立下载和配置的

---

## 推荐打包方案

### 方案 1：单架构 + Windows（最实用）✅

**在 ARM Mac 上：**
```bash
./build_cross_platform.sh 斗破奇兵
```
生成：
- `斗破奇兵-1.0.0-arm64.dmg` (ARM Mac)
- `斗破奇兵 Setup 1.0.0.exe` (Windows)

**Intel Mac 用户怎么办？**
- 可以运行 ARM 版本（通过 Rosetta 2，性能损失 <10%）
- 或者找一台 Intel Mac 单独打包

**优点：**
- 一台机器搞定 90% 的用户
- 简单可靠，易于测试
- Intel Mac 用户可以用 Rosetta 运行

**缺点：**
- Intel Mac 用户需要 Rosetta 2（macOS 11+ 自带）

---

### 方案 2：使用 CI/CD（专业方案）✅

使用 GitHub Actions 在云端打包所有平台：

```yaml
# .github/workflows/build.yml
# 自动在 ARM Mac、Intel Mac、Windows 上分别打包
```

**优点：**
- 完全自动化
- 所有平台原生打包
- 免费（GitHub Actions 有免费额度）

**缺点：**
- 需要配置 CI/CD
- 首次设置稍复杂

---

### 方案 3：多台机器分别打包（最可靠）✅

- ARM Mac → 打包 ARM Mac 版本
- Intel Mac → 打包 Intel Mac 版本  
- Windows → 打包 Windows 版本

**优点：**
- 100% 可靠
- 每个版本都在原生环境测试

**缺点：**
- 需要多台机器
- 手动操作繁琐

---

## 快速开始

### 1. 准备环境

```bash
# 创建 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 安装 Node.js 依赖
cd electron
npm install
cd ..
```

### 2. 选择打包方式

#### A. 推荐：跨平台打包（当前架构 macOS + Windows）

```bash
./build_cross_platform.sh 斗破奇兵
```

#### B. 单平台打包

```bash
# 仅当前架构 macOS
./build_game.sh 斗破奇兵 mac

# 仅 Windows
./build_game.sh 斗破奇兵 win
```

#### C. 手动打包

```bash
# 1. 加载游戏
python game_manager.py load 斗破奇兵

# 2. 打包
cd electron
npm run build:mac-arm    # ARM Mac
npm run build:mac-intel  # Intel Mac
npm run build:win        # Windows
```

---

## 常见问题

### Q1: 在 ARM Mac 上打包的 Intel 版本能用吗？
**A:** 不可靠。虽然能打包，但运行时会报错（架构不匹配）。

### Q2: 在 ARM Mac 上打包的 Windows 版本能用吗？
**A:** 可以！Windows 打包是跨平台的，完全没问题。

### Q3: Intel Mac 用户能用 ARM 版本吗？
**A:** 可以！通过 Rosetta 2 运行，性能损失很小（<10%）。

### Q4: 如何同时支持 ARM 和 Intel Mac？
**A:** 三种方式：
1. 只发布 ARM 版本，Intel 用户用 Rosetta 运行（推荐）
2. 使用 CI/CD 自动打包两个版本
3. 在两台 Mac 上分别打包

### Q5: 打包 Windows 版本需要 wine 吗？
**A:** 不需要。wine 只用于在 macOS 上测试 Windows 程序，不影响打包。

### Q6: 首次打包 Windows 很慢？
**A:** 正常。首次需要下载 Windows 的 Python 依赖（~500MB），后续会快很多。

### Q7: 如何验证 Windows 版本能用？
**A:** 最好在真实 Windows 机器上测试。或者：
```bash
# 安装 wine（可选）
brew install wine-stable

# 在 macOS 上运行 Windows exe（仅基本测试）
wine electron/dist/斗破奇兵\ Setup\ 1.0.0.exe
```

---

## 打包输出

### 文件命名规则

```
electron/dist/
├── <游戏名>-1.0.0-arm64.dmg       # ARM Mac (M1/M2/M3)
├── <游戏名>-1.0.0-x64.dmg         # Intel Mac
└── <游戏名> Setup 1.0.0.exe       # Windows x64
```

### 文件大小参考

- macOS DMG: 200-300 MB
- Windows EXE: 150-250 MB

### 发布建议

**最小发布（推荐）：**
- `<游戏名>-arm64.dmg` (ARM Mac，Intel 可用 Rosetta)
- `<游戏名> Setup.exe` (Windows)

**完整发布：**
- `<游戏名>-arm64.dmg` (ARM Mac)
- `<游戏名>-x64.dmg` (Intel Mac)
- `<游戏名> Setup.exe` (Windows)

---

## 脚本说明

| 脚本 | 用途 | 平台 |
|-----|------|------|
| `build_cross_platform.sh` | 跨平台打包（当前 macOS + Windows） | macOS |
| `build_game.sh` | 单游戏打包（指定平台） | macOS/Linux |
| `build_game.bat` | 单游戏打包（Windows） | Windows |
| `setup_multi_arch.sh` | 多架构环境设置（不推荐） | macOS |

---

## 总结

### 实际建议

**如果你只有一台 ARM Mac：**
```bash
./build_cross_platform.sh 斗破奇兵
```
发布 ARM Mac + Windows 版本，Intel Mac 用户用 Rosetta 运行。

**如果你有多台机器或使用 CI/CD：**
分别打包所有平台，提供最佳体验。

**如果你只关心 Windows：**
在任何平台上都可以打包 Windows 版本。

---

## 技术细节

### Electron Builder 跨平台打包原理

**macOS → Windows ✅**
- Electron Builder 下载 Windows 版本的 Electron
- 使用 wine 或远程构建服务处理 Windows 特定的打包
- Python 依赖独立处理，不依赖 macOS 的 venv

**macOS ARM → macOS Intel ❌**
- 需要复制整个 venv（包含编译好的 .so 文件）
- ARM64 的 .so 无法在 Intel 上运行
- 理论上可以用 Rosetta 创建 x86_64 venv，但不稳定

### 为什么不推荐 Rosetta 方案？

1. **复杂度高**：需要维护两套 venv
2. **不可靠**：某些包在 Rosetta 下编译可能失败
3. **难以测试**：无法在 ARM Mac 上真正测试 Intel 版本
4. **收益低**：Intel Mac 用户可以直接用 Rosetta 运行 ARM 版本

---

## 参考资源

- [Electron Builder 文档](https://www.electron.build/)
- [Python 跨平台打包最佳实践](https://packaging.python.org/)
- [macOS Rosetta 2 文档](https://support.apple.com/en-us/HT211861)
