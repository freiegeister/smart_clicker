import sys
import os
import json
import shutil
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QListWidget, 
                             QMessageBox, QListWidgetItem, QInputDialog, QComboBox,
                             QDialog, QSpinBox, QFormLayout, QDialogButtonBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor

import main as engine
from snipper import SnippingTool
from game_manager import GameManager

# 检测开发者模式
DEV_MODE = os.getenv('DEV_MODE', '0') == '1' or '--dev' in sys.argv

class WorkThread(QThread):
    log_signal = Signal(str)
    
    def __init__(self, config_path, assets_path):
        super().__init__()
        self.config_path = config_path
        self.assets_path = assets_path
        self.running = True  # 添加运行标志
    
    def run(self):
        self.log_signal.emit("🚀 引擎启动中...")
        try:
            # 设置游戏路径
            engine.set_game_paths(self.config_path, self.assets_path)
            
            # 设置停止标志
            engine.STOP_FLAG = False
            
            # 重定向 engine 的日志到 GUI
            import sys
            from io import StringIO
            
            # 创建一个自定义的输出流
            class LogCapture:
                def __init__(self, signal):
                    self.signal = signal
                    self.buffer = ""
                
                def write(self, text):
                    if text and text.strip():
                        self.signal.emit(text.strip())
                    sys.__stdout__.write(text)  # 同时输出到控制台
                
                def flush(self):
                    pass
            
            # 替换 stdout
            old_stdout = sys.stdout
            sys.stdout = LogCapture(self.log_signal)
            
            try:
                # 运行引擎
                engine.main()
            finally:
                # 恢复 stdout
                sys.stdout = old_stdout
                
        except Exception as e:
            import traceback
            err_msg = f"❌ 引擎崩溃: {str(e)}\n{traceback.format_exc()}"
            self.log_signal.emit(err_msg)
            print(err_msg)

    def stop(self):
        """优雅停止线程"""
        self.running = False
        engine.STOP_FLAG = True
        self.log_signal.emit("⏹ 正在停止引擎...")
        # 等待线程自然结束，最多等待3秒
        if not self.wait(3000):
            self.log_signal.emit("⚠️ 引擎未响应，强制终止")
            self.terminate()
        self.wait()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 根据模式设置标题
        title = "Smart Clicker Pro"
        if DEV_MODE:
            title += " [开发者模式]"
        self.setWindowTitle(title)
        self.resize(550, 700)
        
        # 游戏管理器
        self.game_manager = GameManager()
        self.current_game = None
        
        # ... (保持原有的 last_pos 等初始化)
        self.last_pos = None
        self.last_size = None
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 游戏选择区（开发者模式）
        if DEV_MODE:
            game_layout = QHBoxLayout()
            game_layout.addWidget(QLabel("当前游戏："))
            
            self.game_selector = QComboBox()
            self.game_selector.addItem("默认配置")
            self.load_game_list()
            self.game_selector.currentTextChanged.connect(self.on_game_changed)
            game_layout.addWidget(self.game_selector)
            
            btn_new_game = QPushButton("➕ 新建游戏")
            btn_new_game.clicked.connect(self.create_new_game)
            game_layout.addWidget(btn_new_game)
            
            layout.addLayout(game_layout)
        
        # 顶部：状态面板
        self.status_panel = QLabel("准备就绪")
        self.status_panel.setWordWrap(True) # 允许长日志换行
        self.status_panel.setStyleSheet("""
            background-color: #333; 
            color: #00FF00;
            border-radius: 5px; 
            padding: 10px; 
            font-family: Consolas, Monaco, monospace;
            font-size: 12px;
        """)
        self.status_panel.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.status_panel.setMinimumHeight(100)
        layout.addWidget(self.status_panel)
        
        # 中部：规则管理
        layout.addWidget(QLabel("📜 当前生效的识别规则:"))
        self.rule_list = QListWidget()
        self.rule_list.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.rule_list)
        
        btn_refresh = QPushButton("🔄 刷新规则列表")
        btn_refresh.clicked.connect(self.load_rules)
        
        btn_save_default = QPushButton("💾 设为默认规则")
        btn_save_default.setStyleSheet("""
            QPushButton {
                background-color: #34C759; 
                color: white; 
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #248A3D; }
        """)
        btn_save_default.clicked.connect(self.save_as_default)
        
        btn_settings = QPushButton("⚙️ 设置")
        btn_settings.setStyleSheet("""
            QPushButton {
                background-color: #5856D6; 
                color: white; 
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #4644B8; }
        """)
        btn_settings.clicked.connect(self.open_settings)
        
        btn_reset = QPushButton("⚠️ 还原默认规则")
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #FF9500; 
                color: white; 
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #CC7700; }
        """)
        btn_reset.clicked.connect(self.reset_to_default)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_refresh)
        btn_layout.addWidget(btn_save_default)
        btn_layout.addWidget(btn_settings)
        btn_layout.addWidget(btn_reset)
        layout.addLayout(btn_layout)
        
        # 底部：操作区
        action_layout = QVBoxLayout()
        
        self.btn_capture = QPushButton("📷 截图添加素材")
        self.btn_capture.setToolTip("截取新图片并添加到规则库")
        self.btn_capture.setStyleSheet("""
            QPushButton {
                background-color: #007AFF; 
                color: white; 
                padding: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #0062CC; }
        """)
        self.btn_capture.clicked.connect(self.start_capture)
        action_layout.addWidget(self.btn_capture)
        
        self.btn_add_text = QPushButton("🔤 添加文字规则")
        self.btn_add_text.setToolTip("手动输入文字，引擎会通过 OCR 识别并点击")
        self.btn_add_text.setStyleSheet("""
            QPushButton {
                background-color: #5856D6; 
                color: white; 
                padding: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #4644B8; }
        """)
        self.btn_add_text.clicked.connect(self.add_text_rule)
        action_layout.addWidget(self.btn_add_text)
        
        self.btn_start = QPushButton("▶ 启动挂机引擎")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #34C759; 
                color: white; 
                padding: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #248A3D; }
        """)
        self.btn_start.clicked.connect(self.toggle_start)
        action_layout.addWidget(self.btn_start)
        
        layout.addLayout(action_layout)
        
        self.worker = None
        self.load_rules()
    
    def load_game_list(self):
        """加载游戏列表"""
        if not DEV_MODE:
            return
        
        try:
            games = self.game_manager.list_games()
            for game in games:
                self.game_selector.addItem(game['name'])
        except Exception as e:
            self.update_status(f"加载游戏列表失败: {e}")
    
    def on_game_changed(self, game_name):
        """切换游戏"""
        if not DEV_MODE:
            return
        
        if game_name == "默认配置":
            self.current_game = None
        else:
            self.current_game = game_name
        
        self.load_rules()
        self.update_status(f"已切换到: {game_name}")
    
    def create_new_game(self):
        """创建新游戏配置"""
        if not DEV_MODE:
            return
        
        game_name, ok = QInputDialog.getText(
            self,
            "新建游戏",
            "请输入游戏名称：\n\n"
            "提示：\n"
            "• 使用英文或拼音\n"
            "• 避免特殊字符\n"
            "• 例如：game1, my_game"
        )
        
        if not ok or not game_name.strip():
            return
        
        game_name = game_name.strip()
        
        try:
            game_info = self.game_manager.create_game(game_name)
            
            # 添加到选择器
            self.game_selector.addItem(game_name)
            self.game_selector.setCurrentText(game_name)
            
            QMessageBox.information(
                self,
                "✅ 创建成功",
                f"游戏 {game_name} 已创建！\n\n"
                f"目录：{game_info['path']}\n"
                f"配置：{game_info['config']}\n"
                f"资源：{game_info['assets']}"
            )
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建失败: {str(e)}")
    
    def get_config_path(self):
        """获取当前游戏的配置文件路径"""
        if self.current_game:
            game_info = self.game_manager.get_game_info(self.current_game)
            if game_info:
                return game_info['config']
        
        # 使用 current_game 或根目录
        paths = self.game_manager.get_current_game_paths()
        return paths['config']
    
    def get_assets_dir(self):
        """获取当前游戏的资源目录"""
        if self.current_game:
            game_info = self.game_manager.get_game_info(self.current_game)
            if game_info:
                return game_info['assets']
        
        # 使用 current_game 或根目录
        paths = self.game_manager.get_current_game_paths()
        return paths['assets']

    def load_rules(self):
        self.rule_list.clear()
        config_path = self.get_config_path()
        
        if not os.path.exists(config_path):
            self.rule_list.addItem(f"❌ 配置文件不存在: {config_path}")
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            self.rule_list.addItem(f"❌ 致命错误：无法读取配置文件: {e}")
            return
            
        game_name = config.get('game_name', '未知游戏')
        self.setWindowTitle(f"Smart Clicker - {game_name}")
        
        strategies = config.get('strategies', [])
        if not strategies:
            self.rule_list.addItem("⚠️ 当前没有配置任何策略")
            return

        for idx, strategy in enumerate(strategies):
            name = strategy.get('name', '未命名')
            
            # 收集触发图片
            triggers = strategy.get('trigger_images', [])
            if not triggers and strategy.get('trigger_image'):
                triggers.append(strategy.get('trigger_image'))
            
            # 收集触发文字
            trigger_texts = strategy.get('trigger_texts', [])
                
            # 收集前置条件图片
            conditions = strategy.get('condition_images', [])
            if not conditions and strategy.get('condition_image'):
                conditions.append(strategy.get('condition_image'))
            
            # 收集前置条件文字
            condition_texts = strategy.get('condition_texts', [])
            
            # 构建显示文本
            info = f"【策略 {idx+1}】{name}\n"
            
            # 显示触发条件
            if triggers or trigger_texts:
                info += f"   🎯 触发条件:\n"
                if triggers:
                    info += f"      📷 图片 ({len(triggers)}张): {', '.join(triggers)}\n"
                if trigger_texts:
                    info += f"      🔤 文字 ({len(trigger_texts)}个): {', '.join(trigger_texts)}\n"
            else:
                info += f"   ⚠️ 无触发条件（请添加图片或文字）\n"
            
            # 显示前置条件
            if conditions or condition_texts:
                info += f"   🔒 前置条件:\n"
                if conditions:
                    info += f"      📷 图片 ({len(conditions)}张): {', '.join(conditions)}\n"
                if condition_texts:
                    info += f"      🔤 文字 ({len(condition_texts)}个): {', '.join(condition_texts)}\n"
            else:
                info += f"   🔓 无前置条件 (见到就点)\n"
            
            item = QListWidgetItem(info)
            # 根据是否有前置条件给点颜色区分
            if conditions or condition_texts:
                item.setBackground(QColor("#FFF8E1")) # 淡黄
            
            self.rule_list.addItem(item)

    def add_text_rule(self):
        """添加文字识别规则"""
        config_path = self.get_config_path()
        
        if not os.path.exists(config_path):
            QMessageBox.warning(self, "错误", "无法读取配置文件")
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法读取配置文件: {e}")
            return
        
        strategies = config.get('strategies', [])
        if not strategies:
            QMessageBox.warning(self, "错误", "当前没有配置任何策略")
            return
        
        # 第一步：选择策略
        strategy_names = [f"{idx+1}. {s.get('name', '未命名')}" for idx, s in enumerate(strategies)]
        
        strategy_choice, ok = QInputDialog.getItem(
            self, 
            "选择策略", 
            "请选择要添加文字规则的策略：",
            strategy_names, 
            0, 
            False
        )
        
        if not ok or not strategy_choice:
            return
        
        # 获取选中的策略索引
        strategy_idx = int(strategy_choice.split('.')[0]) - 1
        strategy = strategies[strategy_idx]
        
        # 第二步：选择规则类型（触发条件 or 前置条件）
        rule_types = [
            "🎯 触发条件（找到这个文字就点击）",
            "🔒 前置条件（必须先满足这个条件）"
        ]
        
        rule_type, ok = QInputDialog.getItem(
            self,
            "选择规则类型",
            f"为策略「{strategy.get('name')}」添加文字规则：\n\n"
            "• 触发条件：引擎找到这个文字就会点击\n"
            "• 前置条件：必须先满足这个条件才会触发",
            rule_types,
            0,
            False
        )
        
        if not ok or not rule_type:
            return
        
        is_trigger = "触发条件" in rule_type
        
        # 第三步：输入文字
        text, ok = QInputDialog.getText(
            self, 
            "输入文字", 
            "请输入要识别的文字：\n\n"
            "提示：\n"
            "• 支持中英文\n"
            "• 会进行模糊匹配（如输入'关闭'可匹配'关闭广告'）\n"
            "• 建议输入2-4个字\n"
            "• 避免特殊符号"
        )
        
        if not ok or not text.strip():
            return
        
        text = text.strip()
        
        # 添加到配置
        if is_trigger:
            if 'trigger_texts' not in strategy:
                strategy['trigger_texts'] = []
            strategy['trigger_texts'].append(text)
            rule_type_name = "触发条件"
        else:
            if 'condition_texts' not in strategy:
                strategy['condition_texts'] = []
            strategy['condition_texts'].append(text)
            rule_type_name = "前置条件"
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        QMessageBox.information(
            self, 
            "✅ 添加成功", 
            f"已添加文字规则\n\n"
            f"策略：{strategy.get('name')}\n"
            f"类型：{rule_type_name}\n"
            f"文字：{text}\n\n"
            f"注意：\n"
            f"• 首次使用需要安装 easyocr\n"
            f"• 首次运行会下载识别模型\n"
            f"• 文字识别速度较慢（1-3秒）"
        )
        self.load_rules()
    
    def start_capture(self):
        # 1. 保存当前窗口状态
        self.last_pos = self.pos()
        self.last_size = self.size()
        
        # 2. 隐藏主窗口
        self.hide()
        
        # 3. 启动截图工具
        # 注意：snipper 实例必须作为成员变量持有，否则会被垃圾回收导致窗口闪退
        self.snipper = SnippingTool()
        self.snipper.captured.connect(self.on_captured)
        self.snipper.destroyed.connect(self.on_snipper_closed) # 监听关闭事件
        self.snipper.show()

    def on_snipper_closed(self):
        # 只有当窗口真的关闭且没有触发 captured 时（例如按ESC），才需要这里兜底显示
        # 但由于 captured 信号发射后也会 close，为了避免重复 show，我们在 captured 里处理逻辑
        if self.isHidden():
            self.restore_window()

    def restore_window(self):
        self.showNormal() # 强制恢复正常状态，防止全屏残留
        self.activateWindow()
        if self.last_pos:
            self.move(self.last_pos)
            self.resize(self.last_size)

    def on_captured(self, temp_path):
        self.restore_window()
        
        if not os.path.exists(temp_path):
            return

        # 标准化分类逻辑
        options = [
            "🔴 干扰弹窗（最高优先级，见到就点）",
            "🟡 关闭前置条件（检测标志，不点击）",
            "� 关闭按钮（需要前置条件）",
            "� 关闭后置条件（二次确认）",
            "🔵 打开按钮（主动点击）"
        ]
        
        item, ok = QInputDialog.getItem(self, "素材归档", 
                                      "请选择这张图片的作用：\n\n"
                                      "• 干扰弹窗：见到就点，优先级最高\n"
                                      "• 关闭前置条件：检测是否可以关闭的标志\n"
                                      "• 关闭按钮：需要满足前置条件才点击\n"
                                      "• 关闭后置条件：点击关闭后的二次确认\n"
                                      "• 打开按钮：主动观看广告、领取奖励", 
                                      options, 
                                      0, False)
        
        if ok and item:
            timestamp = int(time.time())
            new_filename = ""
            role = ""
            
            if "干扰弹窗" in item:
                new_filename = f"popup_{timestamp}.png"
                role = "popup"
            elif "关闭前置条件" in item:
                new_filename = f"close_pre_{timestamp}.png"
                role = "close_pre"
            elif "关闭按钮" in item:
                new_filename = f"close_{timestamp}.png"
                role = "close"
            elif "关闭后置条件" in item:
                new_filename = f"close_post_{timestamp}.png"
                role = "close_post"
            elif "打开按钮" in item:
                new_filename = f"open_{timestamp}.png"
                role = "open"
                
            target_path = os.path.join(self.get_assets_dir(), new_filename)
            os.makedirs(self.get_assets_dir(), exist_ok=True)
            shutil.move(temp_path, target_path)
            
            self.add_image_to_config(role, new_filename)
            
            QMessageBox.information(self, "✅ 添加成功", f"已归档为: {new_filename}\n规则已更新，下次启动生效。")
            self.load_rules()
        else:
            try: os.remove(temp_path)
            except: pass

    def add_image_to_config(self, role, filename):
        config_path = self.get_config_path()
        
        if not os.path.exists(config_path):
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            return

        # 根据角色找到对应的策略并添加图片
        target_found = False

        # 定义角色到策略名称的映射（标准化）
        role_to_strategy = {
            "popup": "干扰弹窗",
            "close_pre": "关闭前置条件",
            "close": "关闭",
            "close_post": "关闭后置条件",
            "open": "打开"
        }

        strategy_name = role_to_strategy.get(role, "")

        for strategy in config['strategies']:
            if strategy_name and strategy.get('name') == strategy_name:
                # 判断是触发图还是前置条件
                if role == "close_pre":
                    # 关闭前置条件：添加到触发图（用于检测）
                    if 'trigger_images' not in strategy:
                        strategy['trigger_images'] = []
                    strategy['trigger_images'].append(filename)
                elif role == "close":
                    # 关闭按钮：添加到触发图
                    if 'trigger_images' not in strategy:
                        strategy['trigger_images'] = []
                    strategy['trigger_images'].append(filename)
                else:
                    # 其他：添加到触发图
                    if 'trigger_images' not in strategy:
                        strategy['trigger_images'] = []
                    strategy['trigger_images'].append(filename)

                target_found = True
                break

        # 如果没找到对应策略，尝试创建
        if not target_found and strategy_name:
            print(f"警告：未找到策略「{strategy_name}」，请先还原默认配置")

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)


    def toggle_start(self):
        if self.worker is None:
            config_path = self.get_config_path()
            assets_path = self.get_assets_dir()
            
            self.worker = WorkThread(config_path, assets_path)
            self.worker.log_signal.connect(self.update_status)
            self.worker.start()
            self.btn_start.setText("⏹ 停止运行")
            self.btn_start.setStyleSheet("background-color: #FF3B30; color: white; padding: 12px; border-radius: 6px;")
            self.btn_capture.setEnabled(False)
        else:
            self.worker.stop() # 使用封装的 stop
            self.worker = None
            self.btn_start.setText("▶ 启动挂机引擎")
            self.btn_start.setStyleSheet("background-color: #34C759; color: white; padding: 12px; border-radius: 6px;")
            self.btn_capture.setEnabled(True)
            self.status_panel.setText("🚫 引擎已手动停止")

    def update_status(self, msg):
        current_text = self.status_panel.text()
        # 简单的日志滚动，保留最近 5 行
        lines = current_text.split('\n')
        if len(lines) > 5:
            lines = lines[-5:]
        lines.append(msg)
        self.status_panel.setText("\n".join(lines))
    
    def open_settings(self):
        """打开设置对话框"""
        config_path = self.get_config_path()
        
        if not os.path.exists(config_path):
            QMessageBox.warning(self, "错误", "配置文件不存在")
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法读取配置文件: {e}")
            return
        
        # 创建设置对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("⚙️ 引擎设置")
        dialog.resize(400, 200)
        
        layout = QFormLayout(dialog)
        
        # 获取当前设置
        settings = config.get('settings', {})
        current_timeout = settings.get('idle_timeout', 120)
        
        # 空闲超时设置
        timeout_spin = QSpinBox()
        timeout_spin.setMinimum(0)
        timeout_spin.setMaximum(3600)
        timeout_spin.setSingleStep(30)
        timeout_spin.setValue(current_timeout)
        timeout_spin.setSuffix(" 秒")
        timeout_spin.setSpecialValueText("禁用")
        
        timeout_label = QLabel(f"({current_timeout // 60} 分钟)")
        timeout_spin.valueChanged.connect(
            lambda v: timeout_label.setText(f"({v // 60} 分钟)" if v > 0 else "(禁用)")
        )
        
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(timeout_spin)
        timeout_layout.addWidget(timeout_label)
        
        layout.addRow("空闲超时:", timeout_layout)
        
        # 说明文字
        help_text = QLabel(
            "空闲超时: 如果指定时间内没有点击任何目标，引擎将自动停止。\n"
            "设置为 0 表示禁用此功能。"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: gray; font-size: 11px; padding: 10px;")
        layout.addRow(help_text)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        # 显示对话框
        if dialog.exec() == QDialog.Accepted:
            # 保存设置
            new_timeout = timeout_spin.value()
            
            if 'settings' not in config:
                config['settings'] = {}
            
            config['settings']['idle_timeout'] = new_timeout
            
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                timeout_text = f"{new_timeout // 60} 分钟" if new_timeout > 0 else "禁用"
                QMessageBox.information(
                    self,
                    "✅ 保存成功",
                    f"设置已保存！\n\n"
                    f"空闲超时: {timeout_text}\n\n"
                    f"下次启动引擎时生效。"
                )
                self.update_status(f"✅ 已更新设置: 空闲超时 = {timeout_text}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def save_as_default(self):
        """将当前配置保存为默认配置"""
        reply = QMessageBox.question(
            self, 
            "💾 确认保存", 
            "此操作将：\n"
            "1. 将当前配置保存为默认模板\n"
            "2. 覆盖 config_default.json\n"
            "3. 以后可以一键还原到此配置\n\n"
            "是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                config_path = self.get_config_path()
                if os.path.exists(config_path):
                    shutil.copy(config_path, "config_default.json")
                    self.update_status("✅ 已保存为默认规则")
                    QMessageBox.information(
                        self, 
                        "✅ 保存成功", 
                        "当前配置已保存为默认模板！\n\n"
                        "以后可以使用「还原默认规则」按钮恢复到此配置。"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "❌ 保存失败",
                        f"找不到当前配置文件: {config_path}"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "❌ 错误",
                    f"保存失败: {str(e)}"
                )
    
    def reset_to_default(self):
        """还原到默认配置"""
        reply = QMessageBox.question(
            self, 
            "⚠️ 确认还原", 
            "此操作将：\n"
            "1. 清空当前所有规则\n"
            "2. 恢复到默认模板\n"
            "3. 不会删除资源文件夹中的截图\n\n"
            "是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                config_path = self.get_config_path()
                
                # 备份当前配置
                if os.path.exists(config_path):
                    backup_name = f"config_backup_{int(time.time())}.json"
                    backup_path = os.path.join(os.path.dirname(config_path), backup_name)
                    shutil.copy(config_path, backup_path)
                    self.update_status(f"📦 已备份当前配置到: {backup_name}")
                
                # 复制默认配置
                if os.path.exists("config_default.json"):
                    shutil.copy("config_default.json", config_path)
                    self.update_status("✅ 已还原到默认规则")
                    self.load_rules()
                    QMessageBox.information(
                        self, 
                        "✅ 还原成功", 
                        f"已还原到默认配置！\n\n"
                        f"原配置已备份为: {backup_name}\n"
                        f"如需恢复，可手动重命名该文件。"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "❌ 还原失败",
                        "找不到默认配置文件 config_default.json"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "❌ 错误",
                    f"还原失败: {str(e)}"
                )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())