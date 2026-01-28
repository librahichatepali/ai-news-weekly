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
    # 从 GitHub Secrets 读取变量
    sender = os.environ.get('EMAIL_USER') 
    password = os.environ.get('EMAIL_PASS')
    receiver = '249869251@qq.com' # 你的接收邮箱

    # 构建邮件主体，对应你之前的 Email [6] 模块设置
    mail_body = f"""
    <div style="line-height: 1.6; color: #333;">
        <h2 style="color: #007bff; border-bottom: 2px solid #007bff;">🎮 游戏行业价值周报</h2>
        {content}
        <p style="font-size: 12px; color: gray;">生成时间：2026年1月28日</p>
    </div>
    """
    
    msg = MIMEText(mail_body, 'html', 'utf-8')
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = Header('🎮 AI 游戏资讯周报', 'utf-8')

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
