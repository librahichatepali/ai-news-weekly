import feedparser
import smtplib
import os
import ssl
from email.mime.text import MIMEText
from email.header import Header

# 扩展后的 RSS 源列表
FEEDS = [
    "https://www.gcores.com/rss",       # 机核网
    "https://www.gamelook.com.cn/feed", # GameLook
    "https://www.yystv.com/rss/feed"    # 游研社
]

def get_aggregated_news():
    full_content = """
    <div style="background-color: #f4f4f4; padding: 20px; font-family: 'Microsoft YaHei', sans-serif;">
        <h1 style="color: #333; text-align: center;">🎮 游戏与 AI 资讯周报</h1>
        <p style="text-align: center; color: #666;">自动推送系统为您精选今日更新</p>
    """
    
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            source_name = feed.feed.title if 'title' in feed.feed else "未知来源"
            full_content += f'<h2 style="border-left: 5px solid #ff4500; padding-left: 10px; margin-top: 30px;">来源：{source_name}</h2>'
            
            # 每个源抓取 8 条最新的资讯
            for entry in feed.entries[:8]:
                title = entry.title
                link = entry.link
                # 尽量获取更多内容：优先取 content，没有则取 summary
                desc = entry.get('summary', entry.get('description', '暂无详细描述'))
                # 简单清理 HTML 标签防止排版混乱
                if len(desc) > 300:
                    desc = desc[:300] + "..." 
                
                full_content += f"""
                <div style="background: white; padding: 15px; margin-bottom: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3 style="margin: 0;"><a href="{link}" style="color: #007bff; text-decoration: none;">{title}</a></h3>
                    <p style="color: #444; line-height: 1.6; font-size: 14px;">{desc}</p>
                    <a href="{link}" style="font-size: 12px; color: #999;">阅读全文 &raquo;</a>
                </div>
                """
        except Exception as e:
            print(f"解析源 {url} 失败: {e}")

    full_content += "</div>"
    return full_content

def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = '249869251@qq.com' # 或者 tanweilin1987@gmail.com
    
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = f"AI News Bot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header('🎮 游戏与 AI 资讯今日精选', 'utf-8')

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 深度内容周报发送成功！")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    news_html = get_aggregated_news()
    send_mail(news_html)
