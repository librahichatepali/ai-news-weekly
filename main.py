import feedparser
import smtplib
import os
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 【精选垂直源】使用 RSSHub 代理，绕开 GitHub IP 封锁
FEEDS = [
    "https://rsshub.app/sykong/category/25",           # 手游那点事-小游戏专栏
    "https://rsshub.app/gamelook/category/mini-game",   # GameLook-小游戏专题
    "https://rsshub.app/wechat/mp/msgalbum/MzI3MDUyODA3MA==/1587829280459341825" # 微信能量站镜像
]

CORE_KEYWORDS = ["小游戏", "微信", "抖音", "榜单", "题材", "买量", "消耗", "爆款"]
BLACK_LIST = ["主机", "PC", "PS5", "端游", "3A", "芯片", "元宇宙"]

def get_report_content():
    cutoff = datetime.now() - timedelta(days=180) # 回溯半年
    found_articles = []
    
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:50]:
                pub_time = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else None
                if pub_time and pub_time < cutoff: continue
                
                title = entry.title
                summary = entry.get('summary', entry.get('description', '')).lower()
                combined = (title + summary).lower()
                
                if any(w in combined for w in CORE_KEYWORDS) and not any(w in combined for w in BLACK_LIST):
                    if title not in [a['title'] for a in found_articles]:
                        found_articles.append({
                            'title': title,
                            'link': entry.link,
                            'date': pub_time.strftime("%Y-%m-%d") if pub_time else "近期"
                        })
        except: continue

    # 邮件 HTML 模版
    html = f"""
    <div style="max-width: 600px; margin: 0 auto; font-family: sans-serif; border: 1px solid #ddd; border-radius: 8px;">
        <div style="background: #1a73e8; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">🎯 小游戏题材打捞 (Gmail 版)</h2>
            <p style="margin: 5px 0 0; font-size: 12px;">已绕过 QQ 邮箱拦截环境</p>
        </div>
        <div style="padding: 20px;">
            <div style="margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 6px;">
                <strong style="color: #1a73e8;">🔗 官方直达入口 (无拦截风险):</strong><br>
                <a href="https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzI3MDUyODA3MA==&action=getalbum&album_id=1587829280459341825#wechat_redirect" 
                   style="color: #188038; text-decoration: none; font-weight: bold; font-size: 14px;">微信小游戏能量站·往期全集</a>
            </div>
    """

    if not found_articles:
        html += "<p style='text-align:center; color: #666;'>近半年暂未打捞到垂直匹配内容。</p>"
    else:
        for art in found_articles:
            html += f"""
            <div style="margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                <a href="{art['link']}" style="color: #202124; text-decoration: none; font-weight: bold;">• {art['title']}</a>
                <div style="color: #70757a; font-size: 11px; margin-top: 4px;">发布日期: {art['date']}</div>
            </div>
            """
    
    html += "</div></div>"
    return html

def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    
    # 【修改重点】改为你的 Gmail 邮箱
    receiver = 'tanweilin1987@gmail.com' 
    
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = f"MiniGameBot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'📊 小游戏深度情报 - {time.strftime("%m-%d")}', 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print(f"✅ 邮件已发送至 Gmail: {receiver}")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    report_content = get_report_content()
    send_mail(report_content)
