from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

# 加载 Cookie
def load_cookie_str(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            if 'X_COOKIE=' in line:
                return line.split('=', 1)[1].strip().strip("'").strip('"')
    return ""

def get_token_sentiment(ticker):
    print(f"🕵️‍♂️ 正在侦测 {ticker} 的市场情绪...")
    
    options = Options()
    # options.add_argument("--headless=new") # 调试阶段先不隐藏，方便看效果
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # 1. 注入身份
        driver.get("https://x.com")
        cookie_str = load_cookie_str('.env.x')
        for item in cookie_str.split(';'):
            if '=' in item:
                name, val = item.strip().split('=', 1)
                driver.add_cookie({'name': name, 'value': val, 'domain': '.x.com'})
        
        driver.refresh()
        
        # 2. 搜索最新推文
        search_url = f"https://x.com/search?q={ticker}&src=typed_query&f=live"
        driver.get(search_url)
        
        # 等待推文加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
        )
        
        # 3. 抓取数据
        tweets = driver.find_elements(By.CSS_SELECTOR, "article div[data-testid='tweetText']")
        print(f"✅ 抓取到 {len(tweets)} 条实时推文")
        
        raw_texts = [t.text for t in tweets[:10]] # 取前10条
        
        # 4. 简单情绪分析 (关键词打分)
        score = 50 # 初始分
        keywords_bullish = ['moon', 'pump', 'gem', 'bull', '🚀', '💎', 'buy']
        keywords_bearish = ['dump', 'scam', 'rug', 'sell', 'short', '🔻']
        
        for text in raw_texts:
            text_lower = text.lower()
            for k in keywords_bullish:
                if k in text_lower: score += 5
            for k in keywords_bearish:
                if k in text_lower: score -= 5
                
        # 归一化
        score = max(0, min(100, score))
        
        result = {
            "target": ticker,
            "sentiment_score": score,
            "sample_size": len(raw_texts),
            "status": "active" if len(raw_texts) > 0 else "dead"
        }
        
        print(f"📊 分析结果: {result}")
        return result

    except Exception as e:
        print(f"❌ 侦测失败: {e}")
        return {"error": str(e)}
        
    finally:
        driver.quit()

if __name__ == "__main__":
    # 测试一下目前最火的 AI 概念币
    get_token_sentiment("$AI")