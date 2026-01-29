import feedparser
import smtplib
import os
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 【核心源更新】只保留最硬核的垂直渠道，剔除杂闻源
FEEDS = [
    "https://www.gamelook.com.cn/category/mini-game/feed", # GameLook小游戏专栏
    "https://www.vrtuoluo.cn/category/mini-game/feed",    # 游戏陀螺-小游戏频道
    "https://www.youxichaguan.com/feed",                  # 游戏茶馆
    "https://www.dataeye.com/rss",                        # DataEye(数据榜单权威)
    "http://www.sykong.com/feed"                          # 手游那点事
]

# 【白名单】强制标题匹配，确保题材相关性
MUST_HAVE = ["小游戏", "微信", "抖音", "快手", "榜单", "排行榜", "买量", "IAA", "IAP"]
# 【黑名单】强制过滤，不给杂讯机会
IGNORE = ["VR", "AR", "XR", "元宇宙", "盒马", "经济增速", "头显", "Metaverse"]

def get_aggregated_news():
    ten_days_ago = datetime.now() - timedelta(days=10)
    full_content = """
    <div style="max-width: 800px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif;">
        <div style="background: #07C160; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 20px;">🛡️ 纯净版：小游戏题材趋势情报</h1>
            <p style="margin: 5px 0 0; opacity: 0.8;">已自动剔除 36氪、VR 等干扰项，回溯 10 日内精选</p>
        </div>
        <div style="background: white; padding: 20px; border: 1px solid #eee; border-top: none;">
    """
    
    found_articles = []
    
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:50]: # 加大每个源的检索深度
                # 日期回溯逻辑
                published_time = None
                if hasattr(entry, 'published_parsed'):
                    published_time = datetime(*entry.published_parsed[:6])
                
                if published_time and published_time < ten_days_ago:
                    continue

                title = entry.title
                summary = entry.get('summary', entry.get('description', ''))
                combined_text = (title + summary).lower()
                
                # --- 严格过滤逻辑 ---
                # 1. 标题必须包含核心词 或 摘要高频出现核心词
                is_about_minigame = any(word.lower() in title.lower() for word in MUST_HAVE)
                # 2. 绝对不能包含黑名单关键词
                is_irrelevant = any(word.lower() in combined_text for word in IGNORE)
                
                if is_about_minigame and not is_irrelevant:
                    if title not in [a['title'] for a in found_articles]:
                        date_str = published_time.strftime("%m-%d") if published_time else "近期"
                        found_articles.append({
                            'title': title,
                            'link': entry.link,
                            'summary': summary[:350] + "...",
                            'source': f"{feed.feed.get('title', '行业动态')} ({date_str})"
                        })
        except Exception as e:
            print(f"解析 {url} 出错: {e}")

    if not found_articles:
        full_content += "<p style='text-align:center; padding: 50px; color: #999;'>近 10 天核心源暂无符合条件的纯净小游戏资讯。</p>"
    else:
        for art in found_articles:
            full_content += f"""
            <div style="margin-bottom: 25px; padding: 15px; border-left: 5px solid #07C160; background: #fcfcfc; border-radius: 4px;">
                <h3 style="margin: 0 0 10px 0;"><a href="{art['link']}" style="color: #333; text-decoration: none; font-size: 17px;">{art['title']}</a></h3>
                <div style="font-size: 14px; color: #555; line-height: 1.7;">{art['summary']}</div>
                <div style="margin-top: 10px; font-size: 12px; color: #999;">📍 {art['source']}</div>
            </div>
            """

    full_content += "</div></div>"
    return full_content

def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = '249869251@qq.com'
    
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = f"TrendBot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'📊 小游戏垂直情报 (10日精选) - {time.strftime("%m-%d")}', 'utf-8')

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 纯净专报发送成功！")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    news = get_aggregated_news()
    send_mail(news)
