import feedparser
import smtplib
import os
import ssl
from email.mime.text import MIMEText
from email.header import Header

# RSS 源配置
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
            img_url = ""
            if 'image' in entry:
                img_url = entry.image.url
            elif 'media_content' in entry:
                img_url = entry.media_content[0]['url']
            
            img_tag = f'<img src="https://images.weserv.nl/?url={img_url}" style="width:100%;">' if img_url else ""
            full_content += f"<h3>{title}</h3><p>{desc}</p>{img_tag}<br><hr>"
    
    if not full_content:
        full_content = "<h3>系统通知</h3><p>今日暂无新资讯抓取。</p>"
    return full_content

def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    # 使用 strip() 确保彻底清除可能存在的空格
    password = str(os.environ.get('EMAIL_PASS')).strip() 
    receiver = '249869251@qq.com'
    
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = f"NewsBot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header('🎮 AI 游戏资讯周报', 'utf-8')

    # 方案 A: 稳健的 SSL 465 端口
    try:
        print("正在尝试方案 A (SSL 465)...")
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.qq.com", 465, context=context, timeout=20) as server:
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 方案 A 发送成功！")
        return
    except Exception as e:
        print(f"❌ 方案 A 失败: {e}")

    # 方案 B: 备用 TLS 587 端口
    try:
        print("正在尝试方案 B (TLS 587)...")
        server = smtplib.SMTP("smtp.qq.com", 587, timeout=20)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, [receiver], msg.as_string())
        server.quit()
        print("✅ 方案 B 发送成功！")
        return
    except Exception as e:
        print(f"❌ 方案 B 失败: {e}")

    # 方案 C: 终极备用 25 端口 (非加密)
    try:
        print("正在尝试方案 C (普通 25)...")
        server = smtplib.SMTP("smtp.qq.com", 25, timeout=20)
        server.login(sender, password)
        server.sendmail(sender, [receiver], msg.as_string())
        server.quit()
        print("✅ 方案 C 发送成功！")
    except Exception as e:
        print(f"🔥 所有发送方案均已失败。报错详情: {e}")

if __name__ == "__main__":
    news_html = get_aggregated_news()
    send_mail(news_html)
