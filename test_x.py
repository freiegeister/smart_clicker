import requests
import os
import json
from dotenv import load_dotenv

# 加载环境变量 (模拟)
# 实际运行时，我会直接从 .env.x 读取，这里为了演示，直接使用脚本内的逻辑读取文件
def load_env(file_path):
    config = {}
    with open(file_path, 'r') as f:
        for line in f:
            if '=' in line:
                key, val = line.strip().split('=', 1)
                # 去除引号
                if val.startswith("'") and val.endswith("'"): val = val[1:-1]
                if val.startswith('"') and val.endswith('"'): val = val[1:-1]
                config[key] = val
    return config

env = load_env('.env.x')
COOKIE = env.get('X_COOKIE')
CSRF_TOKEN = env.get('X_CSRF_TOKEN')

def test_twitter_post(text):
    print(f"🤖 正在尝试发布推文: {text}")
    
    # 尝试新的 QueryID (通常会定期轮换)
    # 备选列表: 
    # nK1dw4oV3k4w5Tdtc434hQ (CreateTweet)
    # H8_8M7b0W1K7Z63g581K5w (CreateTweet)
    url = "https://x.com/i/api/graphql/nK1dw4oV3k4w5Tdtc434hQ/CreateTweet"
    
    headers = {
        "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA", 
        "content-type": "application/json",
        "cookie": COOKIE,
        "x-csrf-token": CSRF_TOKEN,
        "x-twitter-active-user": "yes",
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-client-language": "en"
    }

    payload = {
        "variables": {
            "tweet_text": text,
            "dark_request": False,
            "media": {
                "media_entities": [],
                "possibly_sensitive": False
            },
            "semantic_annotation_ids": []
        },
        "features": {
            "c9s_tweet_anatomy_moderation_enabled": True,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": True,
            "tweet_awards_web_tipping_enabled": False,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "responsive_web_media_download_video_enabled": False,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_enhance_cards_enabled": False
        },
        "queryId": "nK1dw4oV3k4w5Tdtc434hQ"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"📡 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # 检查是否有错误
            if 'errors' in data and data['errors']:
                print(f"❌ 发布失败: {data['errors'][0]['message']}")
                return False
            
            # 检查是否有数据返回
            if 'data' in data and 'create_tweet' in data['data']:
                tweet_result = data['data']['create_tweet']['tweet_results']['result']
                # 处理不同类型的返回结构（有些可能是 NoteTweet）
                rest_id = tweet_result.get('rest_id')
                print(f"✅ 发布成功! 推文ID: {rest_id}")
                print(f"🔗 链接: https://x.com/user/status/{rest_id}")
                return True
        else:
            print(f"❌ 请求失败: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

if __name__ == "__main__":
    # 发送一条低调的测试推文
    import time
    ts = int(time.time())
    text = f"Hello World. Silicon Pulse system initialization... [{ts}] #AI"
    test_twitter_post(text)