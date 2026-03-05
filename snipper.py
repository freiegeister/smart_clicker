import sys
import cv2
import numpy as np
import os
from PySide6.QtWidgets import (QApplication, QWidget, QRubberBand, QDialog, 
                             QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem)
from PySide6.QtCore import Qt, QRect, QPoint, Signal, QSize
from PySide6.QtGui import QPainter, QColor, QScreen, QGuiApplication, QPixmap, QImage, QCursor

class ImageEditor(QDialog):
    """截图后的编辑窗口，提供多种抠图工具"""
    finished = Signal(str) # 成功保存信号

    def __init__(self, original_pixmap, parent=None):
        super().__init__(parent)
        print("[DEBUG] ImageEditor 初始化中...")
        
        self.setWindowTitle("🎨 截图编辑器")
        self.resize(700, 650)
        self.setModal(True)
        # 确保窗口在最前面
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        # 窗口居中显示
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        
        print(f"[DEBUG] 窗口位置: ({self.x()}, {self.y()}), 尺寸: {self.width()}x{self.height()}")
        
        # 原始数据 - 处理 DPI 缩放
        self.original_pixmap = original_pixmap
        # 设置正确的 devicePixelRatio
        if self.original_pixmap.devicePixelRatio() == 1.0:
            # 检测是否是 Retina 截图（尺寸异常大）
            screen_geo = QGuiApplication.primaryScreen().geometry()
            if self.original_pixmap.width() > screen_geo.width() * 1.5:
                # 可能是 Retina 截图，设置 DPR 为 2
                self.original_pixmap.setDevicePixelRatio(2.0)
                print(f"[DEBUG] 检测到 Retina 截图，设置 DPR=2")
        
        print(f"[DEBUG] 截图尺寸: {self.original_pixmap.width()}x{self.original_pixmap.height()}, DPR: {self.original_pixmap.devicePixelRatio()}")
        
        self.current_image = self.original_pixmap.toImage()
        self.current_image = self.current_image.convertToFormat(QImage.Format_ARGB32)
        
        # 布局
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 大标题提示
        title = QLabel("🎨 截图编辑器")
        title.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #007AFF;
            padding: 10px;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 工具选择区
        tool_layout = QHBoxLayout()
        tool_label = QLabel("选择处理方式：")
        tool_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        tool_layout.addWidget(tool_label)
        
        self.btn_direct = QPushButton("✅ 直接使用（推荐）")
        self.btn_direct.setStyleSheet("""
            QPushButton {
                background-color: #34C759; 
                color: white; 
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #248A3D; }
        """)
        self.btn_direct.clicked.connect(self.save_direct)
        tool_layout.addWidget(self.btn_direct)
        
        self.btn_auto = QPushButton("🤖 智能抠图")
        self.btn_auto.setStyleSheet("""
            QPushButton {
                background-color: #007AFF; 
                color: white; 
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #0062CC; }
        """)
        self.btn_auto.clicked.connect(self.auto_remove_background)
        tool_layout.addWidget(self.btn_auto)
        
        self.btn_manual = QPushButton("🪄 手动魔棒")
        self.btn_manual.setStyleSheet("""
            QPushButton {
                background-color: #FF9500; 
                color: white; 
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #CC7700; }
        """)
        self.btn_manual.clicked.connect(self.enable_manual_mode)
        tool_layout.addWidget(self.btn_manual)
        
        tool_layout.addStretch()
        layout.addLayout(tool_layout)
        
        # 详细提示
        self.tips_label = QLabel(
            "💡 提示：\n"
            "• 直接使用：适合小图标、文字按钮（引擎会自动处理背景）\n"
            "• 智能抠图：自动去除边缘外的背景（适合大部分场景）\n"
            "• 手动魔棒：点击背景区域手动去除（适合复杂背景）"
        )
        self.tips_label.setStyleSheet("""
            background-color: #FFF8E1; 
            color: #333; 
            padding: 12px;
            border-radius: 8px;
            border: 2px solid #FFD700;
            font-size: 12px;
            line-height: 1.5;
        """)
        self.tips_label.setWordWrap(True)
        layout.addWidget(self.tips_label)
        
        # 图片预览区域
        preview_label = QLabel("📸 预览区域")
        preview_label.setStyleSheet("font-weight: bold; color: #666;")
        layout.addWidget(preview_label)
        
        self.view = QGraphicsView()
        self.view.setStyleSheet("""
            QGraphicsView {
                background-color: #F0F0F0;
                border: 2px solid #CCC;
                border-radius: 5px;
            }
        """)
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.pixmap_item = QGraphicsPixmapItem(self.original_pixmap)
        self.scene.addItem(self.pixmap_item)
        
        # 默认不启用手动点击
        self.manual_mode = False
        
        layout.addWidget(self.view)
        
        # 初始化显示（带棋盘格）
        self.update_view()
        
        # 按钮区
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_reset = QPushButton("🔄 还原")
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #8E8E93; 
                color: white; 
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #636366; }
        """)
        self.btn_reset.clicked.connect(self.reset_image)
        
        self.btn_cancel = QPushButton("❌ 取消")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #8E8E93; 
                color: white; 
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #636366; }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_reset)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def save_direct(self):
        """直接保存原图，不做任何处理"""
        self.show_status("✅ 已保存原图（推荐用于小图标）", "#34C759")
        QApplication.processEvents()
        self.save_and_exit()
    
    def reset_image(self):
        """还原到原始图片"""
        self.current_image = self.original_pixmap.toImage().convertToFormat(QImage.Format_ARGB32)
        self.update_view()
        self.show_status("🔄 已还原到原始图片", "#007AFF")
    
    def enable_manual_mode(self):
        """启用手动魔棒模式"""
        self.manual_mode = True
        self.pixmap_item.mousePressEvent = self.on_image_click
        self.pixmap_item.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        self.show_status("🪄 手动模式已启用：左键点击背景去除，右键还原", "#FF9500")
    
    def auto_remove_background(self):
        """智能自动抠图 - 基于边缘检测"""
        self.show_status("⏳ 智能抠图处理中...", "#FF9500")
        QApplication.processEvents()
        
        try:
            # 保存临时文件
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, "temp_auto_process.png")
            self.current_image.save(temp_path)
            
            # 读取图片
            img = cv2.imread(temp_path, cv2.IMREAD_UNCHANGED)
            if img is None:
                self.show_status("❌ 处理失败", "#FF3B30")
                return
            
            # 确保有 alpha 通道
            if len(img.shape) == 2 or img.shape[2] == 3:
                if len(img.shape) == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
                else:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
            
            h, w = img.shape[:2]
            
            # 策略：检测四个角落的颜色，如果相似则认为是背景
            # 取四个角的采样点
            corner_samples = [
                img[0, 0, :3],           # 左上
                img[0, w-1, :3],         # 右上
                img[h-1, 0, :3],         # 左下
                img[h-1, w-1, :3]        # 右下
            ]
            
            # 计算平均背景色
            bg_color = np.mean(corner_samples, axis=0).astype(np.uint8)
            
            # 创建 mask：对于每个像素，如果与背景色相似则标记为背景
            bgr = img[:, :, :3].copy()
            alpha = img[:, :, 3].copy()
            
            # 计算每个像素与背景色的差异
            diff = np.abs(bgr.astype(np.float32) - bg_color.astype(np.float32))
            diff_sum = np.sum(diff, axis=2)
            
            # 阈值：差异小于 40 的认为是背景
            threshold = 40
            background_mask = diff_sum < threshold
            
            # 将背景设为透明
            alpha[background_mask] = 0
            img[:, :, 3] = alpha
            
            # 保存结果
            cv2.imwrite(temp_path, img)
            self.current_image = QImage(temp_path)
            self.update_view()
            
            # 清理
            try:
                os.remove(temp_path)
            except:
                pass
            
            self.show_status("✅ 智能抠图完成！如需调整可使用手动魔棒", "#34C759")
            
        except Exception as e:
            print(f"智能抠图失败: {e}")
            import traceback
            traceback.print_exc()
            self.show_status("❌ 智能抠图失败，请尝试手动模式", "#FF3B30")
    
    def on_image_click(self, event):
        if not self.manual_mode:
            return
            
        pos = event.pos()
        x, y = int(pos.x()), int(pos.y())
        
        if event.button() == Qt.RightButton:
            # 还原
            self.reset_image()
            return

        if event.button() == Qt.LeftButton:
            # 智能魔棒抠图
            self.show_status("⏳ 正在处理，请稍候...", "#FF9500")
            QApplication.processEvents() # 强制刷新界面
            success = self.magic_wand(x, y)
            if success:
                self.show_status("✅ 背景已去除！可继续点击其他区域", "#34C759")
            else:
                self.show_status("❌ 处理失败，请重试", "#FF3B30")
    
    def show_status(self, message, color):
        """在提示区域显示状态消息"""
        self.tips_label.setStyleSheet(f"""
            background-color: {color}; 
            color: white; 
            padding: 12px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
        """)
        self.tips_label.setText(message)
        QApplication.processEvents()

    def magic_wand(self, seed_x, seed_y):
        """使用 OpenCV floodFill 实现魔棒抠图"""
        try:
            # 1. QImage -> Numpy
            width = self.current_image.width()
            height = self.current_image.height()
            
            # 保存为临时文件
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, "temp_edit_buffer.png")
            self.current_image.save(temp_path)
            
            img_cv = cv2.imread(temp_path, cv2.IMREAD_UNCHANGED)
            if img_cv is None: 
                return False
            
            # 如果没有 alpha 通道，增加一个
            if len(img_cv.shape) == 2 or img_cv.shape[2] == 3:
                if len(img_cv.shape) == 2:
                    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_GRAY2BGRA)
                else:
                    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2BGRA)

            # 2. 泛洪填充
            h, w = img_cv.shape[:2]
            if seed_x < 0 or seed_x >= w or seed_y < 0 or seed_y >= h:
                return False

            # OpenCV 的 floodFill 不支持 4 通道，需要分离处理
            # 策略：在 BGR 通道上做 floodFill 获取 mask，然后将 mask 应用到 alpha 通道
            
            # 分离通道 - 必须创建副本，因为 floodFill 需要连续内存
            bgr = img_cv[:, :, :3].copy()  # 前 3 个通道 (BGR)
            alpha = img_cv[:, :, 3].copy()  # alpha 通道
            
            # 创建掩码 (h+2, w+2)
            mask = np.zeros((h+2, w+2), np.uint8)
            
            # 容差 (可调节，值越大去除范围越广)
            diff = (30, 30, 30)  # 只需要 3 个值（BGR）
            
            # 在 BGR 图上做泛洪填充，填充一个临时颜色（用于标记）
            # 我们用一个不太可能出现的颜色，比如纯品红
            temp_color = (255, 0, 255)
            
            cv2.floodFill(bgr, mask, (seed_x, seed_y), temp_color, diff, diff, cv2.FLOODFILL_FIXED_RANGE)
            
            # 3. 将填充区域的 alpha 设为 0（透明）
            # mask 中值为 1 的区域就是被填充的区域（注意 mask 比原图大 2 圈）
            flood_mask = mask[1:-1, 1:-1]  # 去掉边界
            alpha[flood_mask == 1] = 0
            
            # 4. 合并通道
            img_cv[:, :, 3] = alpha

            # 5. Numpy -> QImage
            cv2.imwrite(temp_path, img_cv)
            self.current_image = QImage(temp_path)
            self.update_view()
            
            # 清理
            try:
                os.remove(temp_path)
            except: 
                pass
            
            return True
            
        except Exception as e:
            print(f"抠图失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def update_view(self):
        """更新视图，添加棋盘格背景以显示透明区域"""
        # 创建一个带棋盘格背景的合成图
        width = self.current_image.width()
        height = self.current_image.height()
        
        # 创建棋盘格背景
        checker = QPixmap(width, height)
        painter = QPainter(checker)
        
        # 绘制棋盘格
        checker_size = 10
        for y in range(0, height, checker_size):
            for x in range(0, width, checker_size):
                if (x // checker_size + y // checker_size) % 2 == 0:
                    painter.fillRect(x, y, checker_size, checker_size, QColor(200, 200, 200))
                else:
                    painter.fillRect(x, y, checker_size, checker_size, QColor(255, 255, 255))
        
        # 在棋盘格上绘制当前图片
        painter.drawImage(0, 0, self.current_image)
        painter.end()
        
        self.pixmap_item.setPixmap(checker)

    def save_and_exit(self):
        # 保存到临时文件
        import tempfile
        temp_dir = tempfile.gettempdir()
        save_path = os.path.join(temp_dir, "temp_capture_result.png")
        
        # 检查是否是 Retina 截图（需要缩小到 50%）
        image_to_save = self.current_image
        
        # 如果原始 pixmap 的 DPR 是 2.0，说明是 Retina 截图
        if self.original_pixmap.devicePixelRatio() >= 2.0:
            # 缩小到 50%
            scaled_width = image_to_save.width() // 2
            scaled_height = image_to_save.height() // 2
            image_to_save = image_to_save.scaled(
                scaled_width, 
                scaled_height, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            print(f"[DEBUG] Retina 截图已缩小: {self.current_image.width()}x{self.current_image.height()} → {scaled_width}x{scaled_height}")
        
        success = image_to_save.save(save_path)
        if success:
            print(f"[DEBUG] 图片已保存: {save_path}")
            self.finished.emit(save_path)
            self.accept()
        else:
            QMessageBox.warning(self, "保存失败", "无法保存图片，请重试")



class SnippingTool(QWidget):
    captured = Signal(str) # 信号：流程结束，返回最终路径
    closed_signal = Signal() # 信号：窗口关闭

    def __init__(self, screenshot=None):
        super().__init__()
        print(f"[DEBUG] SnippingTool 初始化，screenshot: {screenshot is not None}")
        
        # 设置无边框、顶层、全屏
        # 移除 Qt.Tool 标志，避免隐藏其他窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 确保窗口能接收键盘事件
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        
        # 使用 showFullScreen 可能会导致某些平台退出时状态混乱，setGeometry 更稳
        screen = QGuiApplication.primaryScreen()
        rect = screen.geometry()
        self.setGeometry(rect)
        
        print(f"[DEBUG] 窗口几何: {rect}")
        
        self.start_point = None
        self.end_point = None
        self.is_snipping = False
        
        # 使用传入的截图，如果没有则抓取当前屏幕
        if screenshot is not None:
            self.original_pixmap = screenshot
            print(f"[DEBUG] 使用传入截图: {screenshot.width()}x{screenshot.height()}")
        else:
            self.original_pixmap = screen.grabWindow(0)
            print(f"[DEBUG] 抓取屏幕: {self.original_pixmap.width()}x{self.original_pixmap.height()}")
        
        # 遮罩颜色
        self.mask_color = QColor(0, 0, 0, 100)
        
        # 设置鼠标
        self.setCursor(Qt.CrossCursor)
        
        print("[DEBUG] SnippingTool 初始化完成")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.original_pixmap)
        
        # 绘制半透明遮罩
        painter.fillRect(self.rect(), self.mask_color)
        
        if self.start_point and self.end_point:
            rect = QRect(self.start_point, self.end_point).normalized()
            # 清除选中区域的遮罩 (挖空)
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            
            # 绘制红框
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(Qt.red)
            painter.drawRect(rect)
            
            # 显示尺寸信息
            painter.setPen(Qt.white)
            info = f"{rect.width()} x {rect.height()}"
            painter.drawText(rect.topLeft() - QPoint(0, 5), info)

    def keyPressEvent(self, event):
        # ESC 退出 - 最高优先级
        if event.key() == Qt.Key_Escape:
            print("[DEBUG] ESC pressed, closing snipper")
            self.closed_signal.emit()
            self.close()
            event.accept()
        # Q 键也可以退出
        elif event.key() == Qt.Key_Q:
            print("[DEBUG] Q pressed, closing snipper")
            self.closed_signal.emit()
            self.close()
            event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.end_point = self.start_point
            self.is_snipping = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_snipping:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_snipping = False
            
            start = self.start_point
            end = self.end_point
            
            # 处理只是点了一下没拖动的情况
            if not start or not end:
                return
                
            rect = QRect(start, end).normalized()
            
            # 最小截图限制
            if rect.width() < 10 or rect.height() < 10:
                self.start_point = None
                self.end_point = None
                self.update()
                return
            
            # 1. 截取原始图
            snipped_pixmap = self.original_pixmap.copy(rect)
            
            # 2. 隐藏截图遮罩窗口 (关键：先隐藏自己，再弹编辑框)
            self.hide()
            
            # 3. 弹出编辑器
            print(f"[DEBUG] 准备打开编辑器，截图尺寸: {snipped_pixmap.width()}x{snipped_pixmap.height()}")
            editor = ImageEditor(snipped_pixmap, None)  # 不设置父窗口，避免继承隐藏状态
            editor.finished.connect(self.on_editor_finished)
            
            # 强制显示并激活
            editor.show()
            editor.raise_()
            editor.activateWindow()
            
            print("[DEBUG] 编辑器已显示，等待用户操作...")
            result = editor.exec()
            print(f"[DEBUG] 编辑器关闭，结果: {result}")
            
            self.close()

    def on_editor_finished(self, path):
        self.captured.emit(path)
    
    def closeEvent(self, event):
        """窗口关闭时发送信号"""
        self.closed_signal.emit()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    snipper = SnippingTool()
    snipper.show()
    sys.exit(app.exec())