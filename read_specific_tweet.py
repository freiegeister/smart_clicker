from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def read_tweet(url):
    print(f"🕵️‍♂️ 正在读取推文: {url} ...")
    
    options = Options()
    options.add_argument("--window-size=1920,1080")
    # options.add_argument("--headless=new") # 调试模式先不隐藏
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # 1. 注入 Cookie
        driver.get("https://x.com")
        with open('.env.x', 'r') as f:
            cookie_str = ""
            for line in f:
                if 'X_COOKIE=' in line:
                    cookie_str = line.split('=', 1)[1].strip().strip("'").strip('"')
                    break
        
        for item in cookie_str.split(';'):
            if '=' in item:
                name, val = item.strip().split('=', 1)
                driver.add_cookie({'name': name, 'value': val, 'domain': '.x.com'})
        
        driver.refresh()
        
        # 2. 访问推文
        driver.get(url)
        time.sleep(5)
        
        # 3. 抓取内容
        try:
            article = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
            )
            text = article.find_element(By.CSS_SELECTOR, "div[data-testid='tweetText']").text
            print(f"✅ 推文内容:\n---\n{text}\n---")
            
            # 尝试抓取图片/视频描述
            try:
                imgs = article.find_elements(By.TAG_NAME, "img")
                print(f"🖼️ 包含 {len(imgs)} 张图片")
            except:
                pass
                
        except Exception as e:
            print(f"⚠️ 无法定位推文内容: {e}")
            driver.save_screenshot("debug_tweet_fail.png")
            
    except Exception as e:
        print(f"❌ 读取失败: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    read_tweet("https://x.com/oberonlai/status/2029204854380667279?s=52")