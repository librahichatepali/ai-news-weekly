import feedparser
import smtplib
import os
import time
from email.mime.text import MIMEText
from email.header import Header

# 重新精选针对“小游戏”和“行业趋势”的源
FEEDS = [
    "https://www.gamelook.com.cn/category/mini-game/feed", # GameLook小游戏专栏
    "https://www.gamelook.com.cn/feed",                  # GameLook全站(用于关键词搜索)
    "https://www.yystv.com/rss/feed"                      # 游研社(备选)
]

# 你最关心的关键词
KEY_WORDS = ["小游戏", "微信", "抖音", "排行榜", "榜单", "上升", "买量", "爆款", "题材"]

def get_aggregated_news():
    full_content = """
    <div style="max-width: 800px; margin: 0 auto; font-family: 'Microsoft YaHei';">
        <h2 style="background: #07C160; color: white; padding: 15px; text-align: center; border-radius: 5px;">
            🚀 小游戏趋势 & 榜单情报
        </h2>
    """
    
    found_articles = []
    
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]: # 扩大扫描范围
                title = entry.title
                summary = entry.get('summary', entry.get('description', ''))
                
                # 核心逻辑：只有标题或摘要包含关键词，才放入周报
                if any(word in title.lower() or word in summary.lower() for word in KEY_WORDS):
                    # 避免重复内容
                    if title not in [a['title'] for a in found_articles]:
                        found_articles.append({
                            'title': title,
                            'link': entry.link,
                            'summary': summary[:400] + "..." if len(summary) > 400 else summary
                        })
        except Exception as e:
            print(f"解析 {url} 出错: {e}")

    if not found_articles:
        full_content += "<p style='text-align:center;'>今日暂未发现匹配小游戏题材的深度信息。</p>"
    else:
        for art in found_articles:
            full_content += f"""
            <div style="margin-bottom: 20px; padding: 15px; border: 1px solid #eee; border-left: 5px solid #07C160;">
                <h3 style="margin-top: 0;"><a href="{art['link']}" style="color: #333; text-decoration: none;">{art['title']}</a></h3>
                <div style="font-size: 14px; color: #666; line-height: 1.6;">{art['summary']}</div>
                <p style="margin-top: 10px;"><a href="{art['link']}" style="color: #07C160;">查看行业详情 →</a></p>
            </div>
            """

    full_content += "</div>"
    return full_content

def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = '249869251@qq.com'
    
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = f"TrendBot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'📊 小游戏题材 & 榜单趋势报告 ({time.strftime("%m-%d")})', 'utf-8')

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 小游戏垂直周报发送成功！")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    news = get_aggregated_news()
    send_mail(news)
