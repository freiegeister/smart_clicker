import cv2
import numpy as np
import pyautogui
import time
import random
import os
import json
import datetime
import mss

# 配置 pyautogui
pyautogui.PAUSE = 0.05  # 每次操作后的暂停时间
pyautogui.FAILSAFE = False  # 禁用鼠标移到角落停止的功能

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

STOP_FLAG = False  # 全局停止标志

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

def click_at(x, y, strategy_name=""):
    """点击指定坐标（使用多种方式确保点击成功）"""
    # 添加随机偏移（±3像素）
    offset_x = random.randint(-3, 3)
    offset_y = random.randint(-3, 3)
    click_x = x + offset_x
    click_y = y + offset_y
    
    # 详细输出：显示策略名和点击坐标
    msg = f"✅ {strategy_name} → ({click_x},{click_y})"
    print(msg)
    log(msg)
    
    try:
        # 方案1：pyautogui (快速但可能被拦截)
        pyautogui.moveTo(click_x, click_y, duration=0.15)
        time.sleep(0.1)
        
        # 使用 mouseDown + mouseUp 代替 click
        pyautogui.mouseDown()
        time.sleep(0.05)
        pyautogui.mouseUp()
        
        log(f"[点击] 点击完成")
        
    except Exception as e:
        # 方案2：macOS 系统命令 (备用，更可靠但较慢)
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Darwin':
                log(f"[点击] pyautogui 失败，尝试 cliclick")
                # 使用 cliclick (需要安装: brew install cliclick)
                subprocess.run(['cliclick', 'c:' + str(click_x) + ',' + str(click_y)], 
                             check=False, capture_output=True)
                log(f"[点击] cliclick 完成")
            else:
                raise e
        except:
            error_msg = f"❌ 点击失败: {e}"
            print(error_msg)
            log(error_msg)
            import traceback
            log(traceback.format_exc())

def find_image_on_screen(img_name, confidence=0.7, debug=False, screen_cache=None):
    """
    高性能识别逻辑 - 使用缓存的截图，单尺度匹配
    """
    img_path = os.path.join(ASSETS_DIR, img_name)
    if not os.path.exists(img_path):
        return None

    try:
        # 使用缓存的截图，避免重复截屏
        if screen_cache is None:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                screen_bgra = np.array(sct_img)
                screen_bgr = cv2.cvtColor(screen_bgra, cv2.COLOR_BGRA2BGR)
        else:
            screen_bgr = screen_cache

        # 读取模板（考虑添加缓存）
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

        # 单尺度匹配 - 最快
        orig_h, orig_w = template_gray.shape[:2]
        
        # 检查尺寸
        if orig_w > screen_gray.shape[1] or orig_h > screen_gray.shape[0]:
            return None

        # 模板匹配
        res = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        
        if max_val >= confidence:
            center_x = max_loc[0] + orig_w // 2
            center_y = max_loc[1] + orig_h // 2
            log(f"✅ {img_name} | 分数:{max_val:.3f} | 坐标:({center_x},{center_y})")
            return (center_x, center_y, 1.0)
        else:
            if max_val > 0.5:
                log(f"❌ {img_name} | 分数:{max_val:.3f} < 阈值:{confidence:.2f}")
            return None
            
    except Exception as e:
        log(f"[错误] {img_name}: {e}")
        return None

def execute_strategy(strategy, screen_cache=None):
    """执行策略 - 使用缓存的截图"""
    action = strategy.get('action', 'click_target')
    confidence = strategy.get('confidence', 0.7)
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
    
    if not triggers:
        return False
    
    # 检查前置条件
    conditions = strategy.get('condition_images', [])
    
    if conditions:
        condition_met = False
        
        # 检查图片前置条件
        for c_img in conditions:
            res = find_image_on_screen(c_img, confidence=confidence, screen_cache=screen_cache)
            if res:
                condition_met = True
                log(f"[前置条件] {c_img}")
                break
        
        if not condition_met:
            return False

    found_location = None

    # 尝试图片匹配
    if triggers:
        for img_name in triggers:
            res = find_image_on_screen(img_name, confidence=confidence, screen_cache=screen_cache)
            if res:
                found_location = (res[0], res[1])
                break
    
    if found_location:
        log(f"[执行] {name}")
        if action == 'click_target':
            click_at(found_location[0], found_location[1], strategy_name=name)
        elif action == 'click_fixed':
            coords = strategy.get('fixed_coords', [0, 0])
            click_at(coords[0], coords[1], strategy_name=name)
        
        if post_delay > 0:
            random_sleep(post_delay)
        return True
            
    return False

def check_precondition_exists(strategies, screen_cache=None):
    """检查是否存在"关闭前置条件"标志 - 使用缓存的截图"""
    for strategy in strategies:
        if strategy.get('name') == '关闭前置条件' and strategy.get('enabled', True):
            triggers = strategy.get('trigger_images', [])
            confidence = strategy.get('confidence', 0.7)
            
            for img in triggers:
                res = find_image_on_screen(img, confidence=confidence, screen_cache=screen_cache)
                if res:
                    log(f"[前置检测] {img}")
                    return True
    
    return False

def main():
    """主循环 - 高性能版本"""
    print("🚀 引擎启动")
    
    # macOS 权限检查
    if os.uname().sysname == 'Darwin':
        try:
            # 测试是否有辅助功能权限
            test_pos = pyautogui.position()
            print(f"✅ 辅助功能权限正常，当前鼠标位置: {test_pos}")
        except Exception as e:
            print(f"⚠️  警告：可能缺少辅助功能权限")
            print(f"   错误: {e}")
            print(f"   请在「系统偏好设置 → 安全性与隐私 → 隐私 → 辅助功能」中")
            print(f"   勾选 Terminal 或 Python")
    
    print("🔄 开始监控...")

    config = load_config()
    if not config:
        print("❌ 无法加载配置文件")
        return

    strategies = config.get('strategies', [])
    if not strategies:
        print("⚠️  配置中没有策略")
        return

    # 显示已启用的策略数量
    enabled_count = len([s for s in strategies if s.get('enabled', True)])
    print(f"📋 已加载 {enabled_count} 个策略")

    # 策略执行顺序
    strategy_order = ['干扰弹窗', '关闭后置条件', '关闭', '打开']

    scan_count = 0
    last_action_time = time.time()
    last_close_time = 0
    idle_timeout = config.get('settings', {}).get('idle_timeout', 300)
    scan_interval = config.get('settings', {}).get('scan_interval', 2.0)

    # 初始化 mss 实例（复用，避免重复创建）
    sct = mss.mss()

    try:
        while True:
            # 检查停止标志
            if STOP_FLAG:
                print("⏹ 收到停止信号")
                break

            scan_count += 1

            # 关键优化：每次扫描只截图一次
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            screen_bgra = np.array(sct_img)
            screen_cache = cv2.cvtColor(screen_bgra, cv2.COLOR_BGRA2BGR)

            # 按优先级执行策略
            action_taken = False

            for priority_name in strategy_order:
                for strategy in strategies:
                    if strategy.get('name') == priority_name:
                        # 特殊处理：关闭策略需要检查前置条件
                        if priority_name == '关闭':
                            conditions = strategy.get('condition_images', [])
                            if not conditions:
                                precondition_met = check_precondition_exists(strategies, screen_cache)
                                if not precondition_met:
                                    log(f"[跳过] 关闭策略 - 前置条件未满足")
                                    continue
                                else:
                                    log(f"[通过] 关闭策略 - 前置条件已满足")

                        # 特殊处理：关闭后置条件只在关闭后3秒内有效
                        if priority_name == '关闭后置条件':
                            if time.time() - last_close_time > 3:
                                continue

                        if execute_strategy(strategy, screen_cache):
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
                print(f"⏰ 空闲超时 ({idle_timeout}秒)")
                break

            # 可中断的扫描间隔
            sleep_time = 0
            while sleep_time < scan_interval:
                if STOP_FLAG:
                    break
                time.sleep(0.1)
                sleep_time += 0.1

    except KeyboardInterrupt:
        print("⚠️  用户中断")
    except Exception as e:
        print(f"❌ 引擎异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sct.close()  # 关闭 mss 实例
        print("🛑 引擎已停止")

if __name__ == "__main__":
    main()
