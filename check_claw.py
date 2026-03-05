from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def check_site():
    print("🚀 启动浏览器检查 claw402.ai ...")
    
    options = Options()
    # options.add_argument("--headless=new") 
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        url = "https://claw402.ai/"
        driver.get(url)
        time.sleep(5) # 等待 JS 加载
        
        title = driver.title
        print(f"📄 页面标题: {title}")
        
        # 截图
        driver.save_screenshot("debug_claw402.png")
        print("📸 截图已保存: debug_claw402.png")
        
        # 获取页面源码
        source = driver.page_source
        print(f"📝 源码长度: {len(source)}")
        
        # 简单打印一下 body 内容
        body_text = driver.find_element("tag name", "body").text
        print(f"👀 页面可见文本: \n---\n{body_text}\n---")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    check_site()