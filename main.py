import feedparser
import smtplib
import os
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 精选源
FEEDS = [
    "https://www.gamelook.com.cn/category/mini-game/feed",
    "https://www.vrtuoluo.cn/category/news/feed",
    "https://www.youxichaguan.com/feed",
    "https://www.dataeye.com/rss",
    "https://36kr.com/feed"
]

WHITE_LIST = ["小游戏", "微信", "抖音", "快手", "榜单", "排行榜", "买量", "爆款", "题材", "研报", "IAA", "IAP"]
BLACK_LIST = ["元宇宙", "Metaverse", "Apple Vision", "神经腕带", "头显", "AR设备"]

def get_aggregated_news():
    # 计算 10 天前的时间戳
    ten_days_ago = datetime.now() - timedelta(days=10)
    
    full_content = """
    <div style="max-width: 800px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif;">
        <div style="background: #07C160; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 22px;">🎯 小游戏行业滚动周报 (10日内精选)</h1>
            <p style="margin: 5px 0 0; opacity: 0.8;">自动回溯近 10 天内的行业题材与榜单趋势</p>
        </div>
        <div style="background: white; padding: 20px; border: 1px solid #eee; border-top: none;">
    """
    
    found_articles = []
    
    for url in FEEDS:
        try:
            print(f"正在扫描: {url}")
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # --- 新增：日期检查逻辑 ---
                # 尝试解析发布日期，如果解析失败则跳过日期检查
                published_time = None
                if hasattr(entry, 'published_parsed'):
                    published_time = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed'):
                    published_time = datetime(*entry.updated_parsed[:6])
                
                # 如果文章早于 10 天前，则直接跳过
                if published_time and published_time < ten_days_ago:
                    continue
                # -------------------------

                title = entry.title
                summary = entry.get('summary', entry.get('description', ''))
                combined_text = (title + summary).lower()
                
                title_useful = any(word.lower() in title.lower() for word in WHITE_LIST)
                content_useful = any(word.lower() in combined_text for word in WHITE_LIST)
                is_annoying = any(word.lower() in combined_text for word in BLACK_LIST)
                
                if (title_useful or content_useful) and not is_annoying:
                    if title not in [a['title'] for a in found_articles]:
                        date_str = published_time.strftime("%m-%d") if published_time else "近期"
                        found_articles.append({
                            'title': title,
                            'link': entry.link,
                            'summary': summary[:400] + "...",
                            'source': f"{feed.feed.get('title', '行业动态')} ({date_str})"
                        })
        except Exception as e:
            print(f"解析 {url} 出错: {e}")

    if not found_articles:
        full_content += "<p style='text-align:center; padding: 50px; color: #999;'>近 10 天内暂无匹配的小游戏垂直资讯。</p>"
    else:
        # 按时间排序（可选，让最新的排在前面）
        for art in found_articles:
            full_content += f"""
            <div style="margin-bottom: 25px; padding: 15px; border-left: 4px solid #07C160; background: #fcfcfc;">
                <h3 style="margin: 0 0 10px 0;"><a href="{art['link']}" style="color: #333; text-decoration: none;">{art['title']}</a></h3>
                <div style="font-size: 14px; color: #666; line-height: 1.7;">{art['summary']}</div>
                <div style="margin-top: 10px; font-size: 12px; color: #999;">来源：{art['source']}</div>
            </div>
            """

    full_content += f"""
            <div style="text-align: center; color: #bbb; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee;">
                本次扫描涵盖了过去 10 天的资讯，共筛选出 {len(found_articles)} 条匹配情报
            </div>
        </div>
    </div>
    """
    return full_content

def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = '249869251@qq.com'
    
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = f"TrendBot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'📊 小游戏 10 日情报精选 ({time.strftime("%m-%d")})', 'utf-8')

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 10日滚动专报发送成功！")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    news_html = get_aggregated_news()
    send_mail(news_html)
