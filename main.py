import feedparser
import smtplib
import os
import time
from email.mime.text import MIMEText
from email.header import Header

# 精选的小游戏行业深度信源
FEEDS = [
    "https://www.gamelook.com.cn/category/mini-game/feed",  # GameLook小游戏专栏
    "https://www.vrtuoluo.cn/feed",                        # 游戏陀螺（含大量小游戏趋势）
    "https://www.youxichaguan.com/feed",                   # 游戏茶馆（小游戏榜单常客）
    "https://www.thepaper.cn/rss_news.jsp?nodeid=25631"    # 澎湃新闻-游戏频道
]

# 核心情报过滤词：只提取包含这些词的资讯
KEY_WORDS = [
    "小游戏", "微信", "抖音", "排行榜", "榜单", "上升", 
    "买量", "爆款", "题材", "转化", "分成", "IAA", "IAP"
]

def get_aggregated_news():
    full_content = """
    <div style="max-width: 800px; margin: 0 auto; background-color: #f9f9f9; font-family: 'Microsoft YaHei', sans-serif; padding: 20px;">
        <div style="background: #07C160; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 24px;">🚀 小游戏题材 & 榜单趋势报告</h1>
            <p style="margin: 5px 0 0; opacity: 0.9;">专注于微信、抖音小游戏行业洞察</p>
        </div>
        <div style="background: white; padding: 20px; border: 1px solid #eee; border-top: none; border-radius: 0 0 8px 8px;">
    """
    
    found_articles = []
    
    for url in FEEDS:
        try:
            print(f"正在扫描: {url}")
            feed = feedparser.parse(url)
            # 扩大扫描范围到每个源的前 25 条，确保不漏掉藏在后面的深度好文
            for entry in feed.entries[:25]:
                title = entry.title
                summary = entry.get('summary', entry.get('description', ''))
                
                # 关键词匹配逻辑
                if any(word.lower() in title.lower() or word.lower() in summary.lower() for word in KEY_WORDS):
                    if title not in [a['title'] for a in found_articles]:
                        found_articles.append({
                            'title': title,
                            'link': entry.link,
                            'summary': summary[:500] + "..." if len(summary) > 500 else summary,
                            'source': feed.feed.get('title', '行业资讯')
                        })
        except Exception as e:
            print(f"解析 {url} 失败: {e}")

    if not found_articles:
        full_content += "<p style='text-align:center; color:#999; padding: 40px;'>今日暂未发现匹配小游戏题材的深度趋势。</p>"
    else:
        for art in found_articles:
            full_content += f"""
            <div style="margin-bottom: 30px; padding: 15px; border-bottom: 1px solid #f0f0f0;">
                <span style="background: #e1f5fe; color: #0288d1; font-size: 12px; padding: 2px 8px; border-radius: 10px;">{art['source']}</span>
                <h3 style="margin: 10px 0;"><a href="{art['link']}" style="color: #333; text-decoration: none; font-size: 18px; line-height: 1.4;">{art['title']}</a></h3>
                <div style="font-size: 14px; color: #555; line-height: 1.8;">{art['summary']}</div>
                <div style="margin-top: 12px;"><a href="{art['link']}" style="color: #07C160; font-weight: bold; text-decoration: none;">查看题材详情 &raquo;</a></div>
            </div>
            """

    full_content += f"""
            <div style="text-align: center; color: #bbb; font-size: 12px; margin-top: 20px;">
                报告生成时间：{time.strftime("%Y-%m-%d %H:%M")} | 总计发现 {len(found_articles)} 条匹配情报
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
    msg['Subject'] = Header(f'📊 小游戏情报: 题材趋势与榜单洞察 ({time.strftime("%m-%d")})', 'utf-8')

    try:
        # 使用 Gmail 稳定通道
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 小游戏垂直情报发送成功！")
    except Exception as e:
        print(f"❌ 发送异常: {e}")

if __name__ == "__main__":
    news_html = get_aggregated_news()
    send_mail(news_html)
