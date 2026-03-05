from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def check_clawhub():
    print("🚀 启动浏览器检查 clawhub.ai/infra403/opentwitter-mcp ...")
    
    options = Options()
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        url = "https://clawhub.ai/infra403/opentwitter-mcp"
        driver.get(url)
        time.sleep(5)
        
        # 截图
        driver.save_screenshot("debug_opentwitter.png")
        print("📸 截图已保存：debug_opentwitter.png")
        
        # 获取页面可见文本
        body_text = driver.find_element("tag name", "body").text
        print(f"\n📄 页面内容:\n{'='*50}\n{body_text[:3000]}\n{'='*50}")
        
    except Exception as e:
        print(f"❌ 错误：{e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    check_clawhub()