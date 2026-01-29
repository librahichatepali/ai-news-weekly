import feedparser
import smtplib
import os
import time
import urllib.request
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 【定向监控池】这里填入你指定的博主，使用 RSSHub 路由转换
# 示例：微信公众号“组件大王”、小红书“小游戏笔记”等
FEEDS = [
    # 微信公众号示例 (需替换为真实路由)
    "https://rsshub.app/wechat/mp/msgalbum/MzI3MDUyODA3MA==/1587829280459341825", # 微信能量站
    "https://rsshub.app/sykong/category/25", # 手游那点事-小游戏专栏
]

# 更加精炼的关键词，只看“爆款”和“题材”
REFINED_KEYWORDS = ["爆款", "题材", "买量", "榜单", "消耗", "微信", "抖音"]

def get_refined_report():
    cutoff = datetime.now() - timedelta(days=180)
    found_articles = []
    
    # 模拟真实浏览器访问
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1'}

    for url in FEEDS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                feed = feedparser.parse(response.read())
                for entry in feed.entries[:20]:
                    pub_time = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else None
                    if pub_time and pub_time < cutoff: continue
                    
                    title = entry.title
                    # 只要标题包含核心词，就判定为精炼干货
                    if any(w in title for w in REFINED_KEYWORDS):
                        found_articles.append({
                            'title': title,
                            'link': entry.link,
                            'date': pub_time.strftime("%m-%d") if pub_time else "精选"
                        })
        except: continue

    html = f"""
    <div style="max-width: 600px; margin: 0 auto; font-family: sans-serif; border: 1px solid #e0e0e0; border-radius: 12px; overflow: hidden;">
        <div style="background: #FF5722; color: white; padding: 20px; text-align: center;">
            <h2 style="margin: 0; font-size: 18px;">🔍 定向博主·题材精炼打捞</h2>
            <p style="margin: 5px 0 0; font-size: 12px; opacity: 0.9;">针对指定自媒体源的深度扫描</p>
        </div>
        <div style="padding: 20px; background: #fff;">
    """

    if not found_articles:
        html += "<p style='text-align:center; color: #999; padding: 30px;'>博主近期暂未发布匹配【爆款/题材】的内容。</p>"
    else:
        for art in found_articles:
            html += f"""
            <div style="margin-bottom: 15px; border-bottom: 1px solid #f5f5f5; padding-bottom: 10px;">
                <a href="{art['link']}" style="color: #333; text-decoration: none; font-weight: bold; font-size: 14px;">• {art['title']}</a>
                <div style="color: #999; font-size: 11px; margin-top: 5px;">📅 发布时间: {art['date']}</div>
            </div>
            """
    
    html += "</div></div>"
    return html

def send_to_gmail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = 'tanweilin1987@gmail.com' # 维持 Gmail 发送以降低拦截
    
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = f"ContentRefiner <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'💎 定向情报精炼 - {time.strftime("%m-%d")}', 'utf-8')
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 精炼报告已发送")
    except Exception as e: print(f"❌ 失败: {e}")

if __name__ == "__main__":
    report = get_refined_report()
    send_to_gmail(report)
