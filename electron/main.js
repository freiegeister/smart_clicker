const { app, BrowserWindow, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

let mainWindow;
let pythonProcess = null;

// 获取Python路径
function getPythonPath() {
  const isDev = !app.isPackaged;
  const isWin = process.platform === 'win32';
  
  if (isDev) {
    // 开发环境：使用项目根目录的venv
    if (isWin) {
      const venvPython = path.join(__dirname, '..', 'venv', 'Scripts', 'python.exe');
      if (fs.existsSync(venvPython)) {
        return venvPython;
      }
      return 'python'; // fallback
    } else {
      const venvPython = path.join(__dirname, '..', 'venv', 'bin', 'python3');
      if (fs.existsSync(venvPython)) {
        return venvPython;
      }
      return 'python3'; // fallback
    }
  } else {
    // 打包环境：使用打包的Python
    const resourcePath = process.resourcesPath;
    if (isWin) {
      return path.join(resourcePath, 'python_app', 'venv', 'Scripts', 'python.exe');
    } else {
      return path.join(resourcePath, 'python_app', 'venv', 'bin', 'python3');
    }
  }
}

// 获取Python脚本路径
function getPythonScriptPath() {
  const isDev = !app.isPackaged;
  
  if (isDev) {
    return path.join(__dirname, '..', 'main.py');
  } else {
    const resourcePath = process.resourcesPath;
    return path.join(resourcePath, 'python_app', 'main.py');
  }
}

// 获取游戏名称
function getGameName() {
  const isDev = !app.isPackaged;
  const configPath = isDev 
    ? path.join(__dirname, '..', 'current_game', 'config.json')
    : path.join(process.resourcesPath, 'python_app', 'current_game', 'config.json');
  
  try {
    if (fs.existsSync(configPath)) {
      const data = fs.readFileSync(configPath, 'utf8');
      const config = JSON.parse(data);
      return config.game_name || 'Smart Clicker';
    }
  } catch (err) {
    console.error('读取游戏名称失败:', err);
  }
  return 'Smart Clicker';
}

function createWindow() {
  const gameName = getGameName();
  
  mainWindow = new BrowserWindow({
    width: 600,
    height: 500,
    resizable: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  mainWindow.setTitle(gameName);
  mainWindow.loadFile('index.html');
  
  // 开发模式打开DevTools
  if (!app.isPackaged) {
    mainWindow.webContents.openDevTools();
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // macOS: 确保 app 已经 ready
  if (app.isReady() && BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC: 启动Python引擎
ipcMain.on('start-engine', (event) => {
  if (pythonProcess) {
    event.reply('engine-log', '⚠️ 引擎已在运行');
    return;
  }

  const pythonPath = getPythonPath();
  const scriptPath = getPythonScriptPath();
  
  event.reply('engine-log', '🚀 引擎启动中...');
  
  pythonProcess = spawn(pythonPath, [scriptPath], {
    cwd: path.dirname(scriptPath)
  });

  pythonProcess.stdout.on('data', (data) => {
    event.reply('engine-log', data.toString().trim());
  });

  pythonProcess.stderr.on('data', (data) => {
    event.reply('engine-log', `❌ ${data.toString().trim()}`);
  });

  pythonProcess.on('close', (code) => {
    event.reply('engine-log', `🛑 引擎已停止 (code: ${code})`);
    event.reply('engine-stopped');
    pythonProcess = null;
  });
});

// IPC: 停止Python引擎
ipcMain.on('stop-engine', (event) => {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM');
    event.reply('engine-log', '⏹ 正在停止引擎...');
  }
});
