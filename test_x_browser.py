from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# 读取 Cookie
def load_cookie_str(file_path):
    config = {}
    with open(file_path, 'r') as f:
        for line in f:
            if 'X_COOKIE=' in line:
                return line.split('=', 1)[1].strip().strip("'").strip('"')
    return ""

COOKIE_STR = load_cookie_str('.env.x')

def post_tweet(text):
    print("🚀 启动浏览器引擎...")
    
    options = Options()
    # options.add_argument("--headless=new") # 调试时可以先注释掉 headless
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print("🌍 打开 Twitter...")
        driver.get("https://x.com")
        
        print("🍪 注入 Cookie...")
        # 解析 Cookie 字符串
        # 格式: k1=v1; k2=v2
        for item in COOKIE_STR.split(';'):
            if '=' in item:
                name, value = item.strip().split('=', 1)
                driver.add_cookie({
                    'name': name,
                    'value': value,
                    'domain': '.x.com'
                })
        
        print("🔄 刷新页面生效...")
        driver.get("https://x.com/home")
        time.sleep(5)
        
        # 检查是否登录成功 (看有没有发推框)
        print("📝 寻找发推框...")
        # X 的输入框通常是一个 contenteditable 的 div
        try:
            input_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
            )
            print("✅ 找到输入框，正在输入...")
            input_box.click()
            input_box.send_keys(text)
            time.sleep(2)
            
            # 点击发送按钮
            # 按钮通常是 data-testid="tweetButtonInline"
            send_btn = driver.find_element(By.CSS_SELECTOR, "button[data-testid='tweetButtonInline']")
            send_btn.click()
            
            print("✅ 点击发送")
            time.sleep(5)
            print("🎉 推文发布流程结束")
            
        except Exception as e:
            print(f"❌ 找不到元素或发送失败: {e}")
            # 截图留证
            driver.save_screenshot("debug_twitter_error.png")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    import time
    ts = int(time.time())
    text = f"Hello World. Silicon Pulse system initialization... [{ts}] #AI"
    post_tweet(text)