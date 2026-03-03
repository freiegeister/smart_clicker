# Electron 打包

## 开发

```bash
python gui.py  # 在项目根目录
```

## 打包

```bash
cd electron
npm install
npm run build
```

输出：`dist/SmartClicker-1.0.0.dmg`

## 注意

- 打包需要 5-10 分钟（正常）
- 只给用户 `.dmg` 文件
- 其他文件都是临时文件
