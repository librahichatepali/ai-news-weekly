import feedparser
import smtplib
import os
from email.mime.text import MIMEText
from email.header import Header

# RSS 源配置
FEEDS = [
    "https://www.gcores.com/rss",
    "https://www.gamelook.com.cn/feed"
]

def get_aggregated_news():
    html_template = ""
    for url in FEEDS:
        feed = feedparser.parse(url)
        # 这里的逻辑对应你之前的 Tools [15] 聚合逻辑
        for entry in feed.entries[:3]: # 每个源取前3条
            title = entry.title
            # 优先获取摘要，如果没有则取正文
            desc = entry.get('summary', entry.get('description', ''))
            # 提取图片 URL (适配不同 RSS 的格式)
            img_url = ""
            if 'image' in entry:
                img_url = entry.image.url
            elif 'media_content' in entry:
                img_url = entry.media_content[0]['url']
            
            # 这里的 HTML 结构完全继承你之前的调试结果
            img_tag = f'<img src="https://images.weserv.nl/?url={img_url}" style="width:100%; max-width:600px;">' if img_url else ""
            html_template += f"""
            <h3>{title}</h3>
            <p>{desc}</p>
            {img_tag}
            <br><hr>
            """
    return html_template

def send_mail(content):
    import smtplib
    sender = os.environ.get('EMAIL_USER')
    password = os.environ.get('EMAIL_PASS').strip()
    receiver = '249869251@qq.com'
    
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = Header('🎮 AI 游戏资讯周报', 'utf-8')

    try:
        # 尝试使用端口 25 (普通模式)，这在云服务器上兼容性有时更好
        server = smtplib.SMTP("smtp.qq.com", 25, timeout=30)
        server.login(sender, password)
        server.sendmail(sender, [receiver], msg.as_string())
        server.quit()
        print("邮件发送成功！")
    except Exception as e:
        print(f"尝试端口25失败: {e}")
        try:
            # 如果 25 不行，最后尝试一次 587 + TLS
            server = smtplib.SMTP("smtp.qq.com", 587, timeout=30)
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
            server.quit()
            print("通过 587 端口发送成功！")
        except Exception as e2:
            print(f"所有端口均尝试失败: {e2}")

    try:
        # QQ 邮箱 SMTP 服务器配置
        with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("邮件发送成功！")
    except Exception as e:
        print(f"发送失败: {e}")

if __name__ == "__main__":
    news = get_aggregated_news()
    if news:
        send_mail(news)
