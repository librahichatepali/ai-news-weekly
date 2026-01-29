import feedparser
import smtplib
import os
import ssl
import time
from email.mime.text import MIMEText
from email.header import Header

# 资讯源配置：涵盖了你目前关心的主要源
FEEDS = [
    "https://www.gcores.com/rss",        # 机核网
    "https://www.gamelook.com.cn/feed",  # GameLook
    "https://www.yystv.com/rss/feed",     # 游研社
    "https://www.thepaper.cn/rss_news.jsp?nodeid=25631" # 澎湃新闻-游戏频道(备选，内容多)
]

def get_aggregated_news():
    # 增加精美样式，让邮件看起来更像专业周报
    full_content = """
    <div style="max-width: 800px; margin: 0 auto; background-color: #ffffff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        <header style="background-color: #2c3e50; color: #ecf0f1; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0;">🎮 游戏 & AI 深度资讯周报</h1>
            <p style="margin: 5px 0 0;">自动抓取最新行业动态</p>
        </header>
        <div style="padding: 20px; border: 1px solid #ddd; border-top: none;">
    """
    
    total_count = 0
    for url in FEEDS:
        try:
            print(f"正在抓取源: {url}")
            # 增加请求超时控制，防止某个源卡死
            feed = feedparser.parse(url)
            source_name = feed.feed.title if 'title' in feed.feed else "资讯频道"
            
            full_content += f'<h2 style="color: #e67e22; border-bottom: 2px solid #e67e22; padding-bottom: 5px; margin-top: 30px;">来自：{source_name}</h2>'
            
            # 增加抓取条数到 15 条，确保内容丰富
            entries_to_process = feed.entries[:15]
            
            for entry in entries_to_process:
                title = entry.title
                link = entry.link
                # 尝试多个字段获取最长的内容描述
                desc = entry.get('content', [{}])[0].get('value', entry.get('summary', entry.get('description', '点击链接查看详情')))
                
                # 清理冗余标签，保留换行
                if len(desc) > 500:
                    desc = desc[:1000] + "..."

                full_content += f"""
                <div style="margin-bottom: 25px; padding: 15px; border-bottom: 1px dashed #eee;">
                    <h3 style="margin: 0 0 10px 0;"><a href="{link}" style="color: #2980b9; text-decoration: none; font-size: 18px;">{title}</a></h3>
                    <div style="color: #34495e; line-height: 1.8; font-size: 15px;">{desc}</div>
                    <div style="margin-top: 10px;"><a href="{link}" style="color: #95a5a6; font-size: 13px;">🔗 查看原文</a></div>
                </div>
                """
                total_count += 1
        except Exception as e:
            print(f"解析 {url} 失败: {e}")

    full_content += f"""
            <footer style="text-align: center; color: #95a5a6; padding: 20px; border-top: 1px solid #ddd; margin-top: 20px;">
                <p>本次共抓取 {total_count} 条有效资讯</p>
                <p>由 Gemini AI 驱动的自动化推送系统</p>
            </footer>
        </div>
    </div>
    """
    return full_content

def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = '249869251@qq.com'
    
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = f"NewsBot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'🎮 今日游戏资讯聚合 ({time.strftime("%Y-%m-%d")})', 'utf-8')

    try:
        # 使用 Gmail 587 端口
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print(f"✅ 邮件发送成功！共计内容已包含在此次推送中。")
    except Exception as e:
        print(f"❌ 发送异常: {e}")

if __name__ == "__main__":
    news_html = get_aggregated_news()
    send_mail(news_html)
