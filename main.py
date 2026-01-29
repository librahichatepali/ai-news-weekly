import feedparser
import smtplib
import os
import time
import urllib.request
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 【博主定向池】已配置你提供的三个核心信源
FEEDS = [
    # 微信公众号：游戏日报 (通过 RSSHub 代理)
    "https://rsshub.app/wechat/mp/msgalbum/MzI3MDUyODA3MA==/1587829280459341825", 
    # 微信公众号：小游戏情报局 (示例占位，由于公众号搜素限制，建议使用 Album 模式)
    "https://rsshub.app/sykong/category/25", 
    # 小红书：她按开始键 (用户 ID: 94136983499)
    "https://rsshub.app/xiaohongshu/user/94136983499"
]

# 针对你提供的博主，进一步精炼关键词
CORE_KEYWORDS = ["小游戏", "题材", "榜单", "爆款", "复盘", "拆解", "买量"]

def get_targeted_report():
    cutoff = datetime.now() - timedelta(days=180) # 维持半年回溯测试
    found_articles = []
    
    # 模拟移动端浏览器头，增加小红书等源的通过率
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
    }

    for url in FEEDS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                feed = feedparser.parse(response.read())
                for entry in feed.entries[:15]:
                    pub_time = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else None
                    if pub_time and pub_time < cutoff: continue
                    
                    title = entry.title
                    # 只要是这几位博主发的，包含任一关键词即保留
                    if any(w in title for w in CORE_KEYWORDS):
                        found_articles.append({
                            'title': title,
                            'link': entry.link,
                            'date': pub_time.strftime("%m-%d") if pub_time else "精选",
                            'source': "自媒体精选"
                        })
        except: continue

    # 构建 Gmail 适配版 HTML
    html = f"""
    <div style="max-width: 600px; margin: 0 auto; font-family: sans-serif; border: 1px solid #eee; border-radius: 10px; overflow: hidden;">
        <div style="background: #6200EE; color: white; padding: 20px; text-align: center;">
            <h2 style="margin: 0; font-size: 18px;">💎 小游戏·博主定向精炼报告</h2>
            <p style="margin: 5px 0 0; font-size: 12px; opacity: 0.8;">监控：游戏日报 | 小游戏情报局 | 她按开始键</p>
        </div>
        <div style="padding: 20px; background: #fff;">
            <div style="margin-bottom: 20px; padding: 12px; background: #fdf2f2; border-left: 4px solid #f44336; font-size: 13px;">
                <strong>⚠️ 手机用户必读：</strong><br>
                由于微信安全策略，请在<strong>手机 Gmail App</strong>中点击文章链接。若在电脑上点击，大概率会提示“未知错误”。
            </div>
    """

    if not found_articles:
        html += "<p style='text-align:center; color: #999; padding: 40px;'>所选博主近期暂无符合【小游戏题材】的更新内容。</p>"
    else:
        for art in found_articles:
            html += f"""
            <div style="margin-bottom: 15px; border-bottom: 1px solid #f0f0f0; padding-bottom: 10px;">
                <span style="background: #6200EE; color: white; font-size: 10px; padding: 2px 6px; border-radius: 4px; margin-right: 8px;">{art['source']}</span>
                <a href="{art['link']}" style="color: #1a73e8; text-decoration: none; font-weight: bold; font-size: 14px;">{art['title']}</a>
                <div style="color: #bbb; font-size: 11px; margin-top: 5px; margin-left: 55px;">📅 {art['date']}</div>
            </div>
            """
    
    html += "</div></div>"
    return html

def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = 'tanweilin1987@gmail.com'
    
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = f"RefinedBot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'🚀 博主情报精炼 - {time.strftime("%m-%d")}', 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 发送成功")
    except Exception as e: print(f"❌ 失败: {e}")

if __name__ == "__main__":
    report = get_targeted_report()
    send_mail(report)
