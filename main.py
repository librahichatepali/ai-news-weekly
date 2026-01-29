import feedparser
import smtplib
import os
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header

# 【保底策略】选取全球访问最稳定的聚合源，监控所有转载 DataEye 榜单的渠道
FEEDS = [
    "https://rsshub.app/sykong/news",                      # 手游那点事 (转载DataEye最稳)
    "https://www.gamelook.com.cn/category/mini-game/feed",  # GameLook
    "https://www.vrtuoluo.cn/category/mini-game/feed",     # 游戏陀螺
    "https://rsshub.app/xueqiu/user/stock/小游戏"           # 雪球专题
]

MUST_KEYWORDS = ["榜单", "排行榜", "Top", "买量", "微信", "DataEye", "爆款"]

def get_aggregated_news():
    # 回溯 30 天，确保不错过重磅月报
    cutoff = datetime.now() - timedelta(days=30)
    
    full_content = """
    <div style="max-width: 800px; margin: 0 auto; font-family: 'Microsoft YaHei', sans-serif; background: #f4f4f4; padding: 15px;">
        <div style="background: #07C160; color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0;">
            <h1 style="margin: 0; font-size: 20px;">🎮 小游戏实时榜单 & 行业雷达</h1>
            <p style="margin: 5px 0 0; opacity: 0.8; font-size: 13px;">每日自动更新 · 聚合 DataEye 与垂直媒体数据</p>
        </div>
        
        <div style="background: white; padding: 20px; margin-bottom: 15px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 12px 12px;">
            <h2 style="font-size: 16px; color: #333; border-left: 4px solid #07C160; padding-left: 10px; margin-bottom: 15px;">🚀 实时榜单入口 (点击即达)</h2>
            <div style="display: flex; justify-content: space-around; text-align: center;">
                <div style="flex: 1;">
                    <a href="https://www.dataeye.com/report" style="text-decoration: none; color: #07C160;">
                        <div style="font-weight: bold; font-size: 14px;">DataEye</div>
                        <div style="font-size: 11px; color: #999;">买量/消耗榜单</div>
                    </a>
                </div>
                <div style="flex: 1; border-left: 1px solid #eee;">
                    <a href="https://www.aldzs.com/toplist" style="text-decoration: none; color: #07C160;">
                        <div style="font-weight: bold; font-size: 14px;">阿拉丁</div>
                        <div style="font-size: 11px; color: #999;">微信指数排名</div>
                    </a>
                </div>
                <div style="flex: 1; border-left: 1px solid #eee;">
                    <a href="https://index.bilibili.com/" style="text-decoration: none; color: #07C160;">
                        <div style="font-weight: bold; font-size: 14px;">B站指数</div>
                        <div style="font-size: 11px; color: #999;">玩家热度趋势</div>
                    </a>
                </div>
            </div>
        </div>
    """
    
    found_articles = []

    # 尝试从影子源打捞文章
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:80]:
                pub_time = None
                if hasattr(entry, 'published_parsed'):
                    pub_time = datetime(*entry.published_parsed[:6])
                if pub_time and pub_time < cutoff: continue

                title = entry.title
                summary = entry.get('summary', entry.get('description', ''))
                combined = (title + summary).lower()
                
                if any(w.lower() in combined for w in MUST_KEYWORDS):
                    if title not in [a['title'] for a in found_articles]:
                        found_articles.append({
                            'title': title,
                            'link': entry.link,
                            'summary': summary[:300] + "...",
                            'source': f"{feed.feed.get('title', '行业源')} ({pub_time.strftime('%m-%d') if pub_time else '近期'})"
                        })
        except: continue

    # 资讯部分
    full_content += '<div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0;">'
    full_content += '<h2 style="font-size: 16px; color: #333; border-left: 4px solid #ff9800; padding-left: 10px; margin-bottom: 15px;">🗞️ 深度研报 & 文章打捞</h2>'
    
    if not found_articles:
        full_content += "<p style='text-align:center; padding: 30px; color: #999; font-size: 13px;'>近 30 天内暂无匹配的深度分析文章，建议通过上方入口查看实时数据。</p>"
    else:
        for art in found_articles:
            is_heavy = "DataEye" in art['title'] or "榜单" in art['title']
            style = "border-bottom: 1px solid #f0f0f0; padding: 15px 0;"
            full_content += f"""
            <div style="{style}">
                <h3 style="margin: 0 0 8px 0; font-size: 15px;"><a href="{art['link']}" style="color: #2c3e50; text-decoration: none;">{'[重磅] ' if is_heavy else ''}{art['title']}</a></h3>
                <div style="font-size: 12px; color: #666; line-height: 1.5;">{art['summary']}</div>
                <div style="margin-top: 8px; font-size: 11px; color: #999;">📅 {art['source']}</div>
            </div>
            """
    
    full_content += "</div></div>"
    return full_content

def send_mail(content):
    sender = os.environ.get('EMAIL_USER')
    password = str(os.environ.get('EMAIL_PASS')).strip()
    receiver = '249869251@qq.com'
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = f"SmallGameBot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = Header(f'📊 小游戏实时榜单专报 - {time.strftime("%m-%d")}', 'utf-8')
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("✅ 发送成功！")
    except Exception as e: print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    news_html = get_aggregated_news()
    send_mail(news_html)
