import cv2
import numpy as np
import pyautogui
import time
import random
import os
import json
import datetime
import mss

# 基础配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "debug.log")

from game_manager import GameManager
_game_manager = GameManager()
_game_paths = _game_manager.get_current_game_paths()

ASSETS_DIR = _game_paths['assets']
CONFIG_FILE = _game_paths['config']

def set_game_paths(config_path, assets_path):
    """设置游戏路径（由 GUI 调用）"""
    global ASSETS_DIR, CONFIG_FILE
    CONFIG_FILE = config_path
    ASSETS_DIR = assets_path
    os.makedirs(ASSETS_DIR, exist_ok=True)

OCR_READER = None
STOP_FLAG = False  # 全局停止标志

def init_ocr():
    """初始化 OCR 引擎"""
    global OCR_READER
    if OCR_READER is not None:
        return True
    
    try:
        import easyocr
        log("[OCR] 正在初始化文字识别引擎...")
        OCR_READER = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=False)
        log("[OCR] 文字识别引擎初始化成功")
        return True
    except ImportError:
        log("[OCR] 未安装 easyocr，文字识别功能不可用")
        log("[OCR] 安装命令: pip install easyocr")
        return False
    except Exception as e:
        log(f"[OCR] 初始化失败: {e}")
        return False

def find_text_on_screen(text, confidence=0.6):
    """在屏幕上查找文字"""
    global OCR_READER
    
    # 延迟初始化 OCR
    if OCR_READER is None:
        if not init_ocr():
            return None
    
    try:
        # 截图
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            screen_bgra = np.array(sct_img)
            screen_bgr = cv2.cvtColor(screen_bgra, cv2.COLOR_BGRA2BGR)
        
        # OCR 识别
        results = OCR_READER.readtext(screen_bgr)
        
        # 查找匹配的文字
        for (bbox, detected_text, conf) in results:
            if text in detected_text and conf >= confidence:
                # 计算中心点
                top_left = bbox[0]
                bottom_right = bbox[2]
                center_x = int((top_left[0] + bottom_right[0]) / 2)
                center_y = int((top_left[1] + bottom_right[1]) / 2)
                
                log(f"✅ OCR识别成功: 找到目标文字 | 置信度:{conf:.2f} | 坐标:({center_x},{center_y})")
                return (center_x, center_y, 1.0)
        
        return None
        
    except Exception as e:
        log(f"[错误] OCR识别异常: {e}")
        return None


def log(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except:
        pass

def random_sleep(base_s):
    delay = random.uniform(base_s * 0.8, base_s * 1.2)
    time.sleep(delay)

def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log(f"[致命错误] 无法读取配置文件: {e}")
        return None

def get_click_scale():
    """获取点击坐标缩放系数"""
    try:
        with mss.mss() as sct:
            phys_w = sct.monitors[1]['width']
        logic_w, _ = pyautogui.size()
        return phys_w / logic_w
    except Exception:
        return 2.0

CLICK_SCALE = get_click_scale()

def click_at(x, y):
    """点击指定坐标（物理像素 -> 逻辑像素）"""
    logic_x = int(x / CLICK_SCALE)
    logic_y = int(y / CLICK_SCALE)
    
    # 添加随机偏移（±3像素）
    offset_x = random.randint(-3, 3)
    offset_y = random.randint(-3, 3)
    logic_x += offset_x
    logic_y += offset_y
    
    log(f"🖱️ 点击: 物理({x},{y}) -> 逻辑({logic_x},{logic_y}) [Scale:{CLICK_SCALE:.1f}]")
    pyautogui.moveTo(logic_x, logic_y, duration=0.1)
    pyautogui.click()

def find_image_on_screen(img_name, confidence=0.6, debug=False):
    """
    简化识别逻辑 - 专注解决背景色变化问题
    使用边缘检测，对背景色完全不敏感
    """
    img_path = os.path.join(ASSETS_DIR, img_name)
    if not os.path.exists(img_path):
        return None

    try:
        # 1. 屏幕截图
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            screen_bgra = np.array(sct_img)
            screen_bgr = cv2.cvtColor(screen_bgra, cv2.COLOR_BGRA2BGR)

        # 2. 读取模板
        template_raw = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if template_raw is None:
            return None

        # 处理 Alpha 通道
        if len(template_raw.shape) == 3 and template_raw.shape[2] == 4:
            template_bgr = template_raw[:, :, :3]
        else:
            template_bgr = template_raw
        
        # 转灰度
        template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
        screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
        
        # 边缘检测 - 关键：对背景色完全不敏感
        template_edges = cv2.Canny(template_gray, 50, 150)
        screen_edges = cv2.Canny(screen_gray, 50, 150)

        # 只测试两个尺度：1.0 和 0.9（减少计算量）
        scales = [1.0, 0.9]
        
        best_val = 0.0
        best_match = None
        best_scale = 1.0
        best_w, best_h = 0, 0

        for scale in scales:
            width = int(template_bgr.shape[1] * scale)
            height = int(template_bgr.shape[0] * scale)
            
            if width < 10 or height < 10:
                continue
            if width > screen_bgr.shape[1] or height > screen_bgr.shape[0]:
                continue

            # 缩放
            if scale == 1.0:
                curr_edges = template_edges
                curr_gray = template_gray
            else:
                curr_edges = cv2.resize(template_edges, (width, height))
                curr_gray = cv2.resize(template_gray, (width, height))

            # 边缘匹配（主要方法）
            try:
                res = cv2.matchTemplate(screen_edges, curr_edges, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                val_edge = max_val
                loc_edge = max_loc
            except:
                val_edge = 0
                loc_edge = (0, 0)
            
            # 灰度匹配（辅助验证）
            try:
                res = cv2.matchTemplate(screen_gray, curr_gray, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                val_gray = max_val
                loc_gray = max_loc
            except:
                val_gray = 0
                loc_gray = (0, 0)
            
            # 综合评分：边缘70% + 灰度30%
            val = val_edge * 0.7 + val_gray * 0.3
            loc = loc_edge if val_edge > val_gray else loc_gray

            if val > best_val:
                best_val = val
                best_match = loc
                best_scale = scale
                if scale == 1.0:
                    best_h, best_w = template_bgr.shape[:2]
                else:
                    best_h, best_w = height, width

        # 降低阈值，因为边缘匹配分数通常较低
        final_threshold = max(0.4, confidence - 0.2)

        if best_val >= final_threshold:
            center_x = best_match[0] + best_w // 2
            center_y = best_match[1] + best_h // 2
            log(f"✅ {img_name} | 分数:{best_val:.2f} | 坐标:({center_x},{center_y})")
            return (center_x, center_y, best_scale)
        else:
            if best_val > 0.2:
                log(f"⚠️ {img_name} | 分数:{best_val:.2f} < 阈值:{final_threshold:.2f}")
            return None
            
    except Exception as e:
        log(f"[错误] {img_name}: {e}")
        return None

def execute_strategy(strategy):
    """执行策略"""
    action = strategy.get('action', 'click_target')
    confidence = strategy.get('confidence', 0.6)
    post_delay = strategy.get('post_delay', 1)
    name = strategy.get('name', '未命名策略')
    enabled = strategy.get('enabled', True)
    
    # 跳过禁用的策略
    if not enabled:
        return False
    
    # 如果 action 是 none，跳过执行
    if action == 'none':
        return False
    
    # 检查是否有触发条件
    triggers = strategy.get('trigger_images', [])
    trigger_texts = strategy.get('trigger_texts', [])
    
    if not triggers and not trigger_texts:
        return False
    
    # 检查前置条件
    conditions = strategy.get('condition_images', [])
    condition_texts = strategy.get('condition_texts', [])
    
    if conditions or condition_texts:
        condition_met = False
        
        # 检查图片前置条件
        for c_img in conditions:
            res = find_image_on_screen(c_img, confidence=confidence)
            if res:
                condition_met = True
                log(f"[前置条件] {c_img}")
                break
        
        # 检查文字前置条件
        if not condition_met and condition_texts:
            for c_text in condition_texts:
                res = find_text_on_screen(c_text, confidence=confidence)
                if res:
                    condition_met = True
                    log(f"[前置条件] 文字匹配")
                    break
        
        if not condition_met:
            return False

    found_location = None

    # 优先尝试图片匹配
    if triggers:
        for img_name in triggers:
            res = find_image_on_screen(img_name, confidence=confidence)
            if res:
                found_location = (res[0], res[1])
                break
    
    # 如果图片没找到，尝试文字匹配
    if not found_location and trigger_texts:
        for text in trigger_texts:
            res = find_text_on_screen(text, confidence=confidence)
            if res:
                found_location = (res[0], res[1])
                log(f"[触发文字] 找到目标")
                break
    
    if found_location:
        log(f"[执行] {name}")
        if action == 'click_target':
            click_at(found_location[0], found_location[1])
        elif action == 'click_fixed':
            coords = strategy.get('fixed_coords', [0, 0])
            click_at(coords[0] * CLICK_SCALE, coords[1] * CLICK_SCALE)
        
        if post_delay > 0:
            random_sleep(post_delay)
        return True
            
    return False

def check_precondition_exists(strategies):
    """检查是否存在"关闭前置条件"标志"""
    for strategy in strategies:
        if strategy.get('name') == '关闭前置条件' and strategy.get('enabled', True):
            triggers = strategy.get('trigger_images', [])
            confidence = strategy.get('confidence', 0.6)
            
            for img in triggers:
                res = find_image_on_screen(img, confidence=confidence)
                if res:
                    log(f"[前置检测] {img}")
                    return True
    
    return False

def main():
    """主循环"""
    log("=" * 60)
    log("🚀 Smart Clicker 引擎启动")
    log("=" * 60)

    config = load_config()
    if not config:
        log("❌ 无法加载配置文件")
        return

    strategies = config.get('strategies', [])
    if not strategies:
        log("⚠️  配置中没有策略")
        return

    # 显示已启用的策略数量
    enabled_count = len([s for s in strategies if s.get('enabled', True)])
    log(f"📋 已加载 {enabled_count} 个策略")
    log("🔄 开始监控...\n")

    # 策略执行顺序
    strategy_order = ['干扰弹窗', '关闭后置条件', '关闭', '打开']

    scan_count = 0
    last_action_time = time.time()
    last_close_time = 0
    idle_timeout = config.get('settings', {}).get('idle_timeout', 300)
    scan_interval = config.get('settings', {}).get('scan_interval', 1)

    try:
        while True:
            # 检查停止标志
            if STOP_FLAG:
                log("\n⏹ 收到停止信号")
                break

            scan_count += 1

            # 按优先级执行策略
            action_taken = False

            for priority_name in strategy_order:
                for strategy in strategies:
                    if strategy.get('name') == priority_name:
                        # 特殊处理：关闭策略需要检查前置条件
                        if priority_name == '关闭':
                            conditions = strategy.get('condition_images', [])
                            if not conditions:
                                if not check_precondition_exists(strategies):
                                    continue

                        # 特殊处理：关闭后置条件只在关闭后3秒内有效
                        if priority_name == '关闭后置条件':
                            if time.time() - last_close_time > 3:
                                continue

                        if execute_strategy(strategy):
                            action_taken = True
                            last_action_time = time.time()

                            # 记录关闭时间
                            if priority_name == '关闭':
                                last_close_time = time.time()

                            break

                if action_taken:
                    break

            # 检查空闲超时
            idle_time = time.time() - last_action_time
            if idle_timeout > 0 and idle_time > idle_timeout:
                log(f"\n⏰ 空闲超时 ({idle_timeout}秒)")
                break

            # 可中断的扫描间隔
            sleep_time = 0
            while sleep_time < scan_interval:
                if STOP_FLAG:
                    break
                time.sleep(0.1)
                sleep_time += 0.1

    except KeyboardInterrupt:
        log("\n⚠️  用户中断")
    except Exception as e:
        log(f"\n❌ 引擎异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        log("\n" + "=" * 60)
        log("🛑 引擎已停止")
        log("=" * 60)

if __name__ == "__main__":
    main()
