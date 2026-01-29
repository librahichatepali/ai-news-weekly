import feedparser
import smtplib
import os
from email.mime.text import MIMEText
from email.header import Header

# RSS 源
FEEDS = [
    "https://www.gcores.com/rss",
    "https://www.gamelook.com.cn/feed"
]

def get_aggregated_news():
    full_content = ""
    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            title = entry.title
            desc = entry.get('summary', entry.get('description', '暂无摘要'))
            full_content += f"<h3>{title}</h3><p>{desc}</p><br><hr>"
    
    if not full_content:
        full_content = "<h3>系统通知</h3><p>今日暂无新资讯抓取。</p>"
    return full_content

def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = '249869251@qq.com' # 接收方可以维持 QQ 邮箱
    
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = Header('🎮 游戏资讯周报 (Gmail 转发)', 'utf-8')

    try:
        # Gmail 专用配置
        print(f"正在通过 Gmail ({sender}) 发送邮件...")
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
            server.starttls() # 开启加密
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 邮件通过 Gmail 发送成功！")
    except Exception as e:
        print(f"🔥 Gmail 发送也失败了: {e}")

if __name__ == "__main__":
    news_html = get_aggregated_news()
    send_mail(news_html)
