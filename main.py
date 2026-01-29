import feedparser
import smtplib
import os
import time
import urllib.request
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 【直接源】不再通过代理，改用直接抓取+浏览器伪装
FEEDS = [
    "http://www.sykong.com/feed",                          # 手游那点事-小游戏
    "https://www.gamelook.com.cn/category/mini-game/feed",  # GameLook
    "https://www.youxichaguan.com/feed"                    # 游戏茶馆
]

CORE_KEYWORDS = ["小游戏", "微信", "抖音", "榜单", "排行", "买量", "爆款", "题材"]
BLACK_LIST = ["PS5", "主机", "端游", "芯片", "元宇宙"]

def get_report():
    cutoff = datetime.now() - timedelta(days=180) # 维持半年回溯
    found_articles = []
    
    # 设置浏览器伪装头，防止被封锁
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    for url in FEEDS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read()
                feed = feedparser.parse(content)
                for entry in feed.entries[:40]:
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
        except Exception as e:
            print(f"抓取 {url} 失败: {e}")
            continue

    # 构建 Gmail 适配版 HTML
    html = f"""
    <div style="max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <div style="background-color: #1a73e8; color: white; padding: 24px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0; font-size: 20px;">🎮 小游戏题材 & 榜单情报站</h2>
            <p style="margin: 8px 0 0; font-size: 13px; opacity: 0.9;">已针对 Gmail 优化显示 | 回溯 180 天</p>
        </div>
        
        <div style="padding: 20px; background-color: white; border: 1px solid #dadce0; border-top: none; border-radius: 0 0 8px 8px;">
            <div style="margin-bottom: 24px; padding: 16px; background-color: #f8f9fa; border-left: 4px solid #34a853; border-radius: 4px;">
                <strong style="color: #202124; font-size: 14px;">💡 官方总目录 (最稳入口):</strong><br>
                <p style="font-size: 12px; color: #5f6368; margin: 8px 0;">若下方链接在电脑上无法打开，请在手机微信中点击此链接：</p>
                <a href="https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzI3MDUyODA3MA==&action=getalbum&album_id=1587829280459341825#wechat_redirect" 
                   style="color: #1a73e8; text-decoration: none; font-weight: bold;">➡️ 微信官方·小游戏能量站专辑</a>
            </div>
    """

    if not found_articles:
        html += "<div style='text-align:center; padding: 40px; color: #70757a;'>⚠️ 暂未捕获到符合条件的垂直资讯。<br>建议通过上方官方目录查看。</div>"
    else:
        for art in found_articles:
            html += f"""
            <div style="margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #e8eaed;">
                <a href="{art['link']}" target="_blank" style="color: #1a0dab; text-decoration: none; font-size: 16px; font-weight: 500;">• {art['title']}</a>
                <div style="color: #70757a; font-size: 12px; margin-top: 6px;">⏱ {art['date']}</div>
            </div>
            """
    
    html += "</div><div style='text-align: center; font-size: 11px; color: #9aa0a6; padding: 16px;'>Data Services by Gemini Intelligence</div></div>"
    return html

def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = 'tanweilin1987@gmail.com'  # 确认发送至 Gmail
    
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = f"SmallGameRadar <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'📊 小游戏题材情报 - {time.strftime("%m-%d")}', 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print(f"✅ 发送成功")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    report_content = get_report()
    send_mail(report_content)
